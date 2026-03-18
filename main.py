import asyncio
import json
import os
import secrets
from datetime import datetime
import qrcode
from io import BytesIO
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, BufferedInputFile
from config import BOT_TOKEN

# ---------- Конфигурация ----------
ADMIN_IDS = [601800743]  # замените на свой Telegram ID
DATA_FILE = "registrations.json"
USERS_FILE = "users.json"

# ---------- Инициализация бота ----------
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())


# ---------- Состояния FSM ----------
class Registration(StatesGroup):
    event = State()
    name = State()
    contact = State()
    confirm = State()
    choose_next = State()
    change_name = State()
    change_contact = State()


# ---------- Клавиатуры ----------
def get_main_menu_keyboard():
    """Главное меню после /start"""
    buttons = [
        [KeyboardButton(text="ℹ️ Информация о мероприятиях")],
        [KeyboardButton(text="📝 Зарегистрироваться на мероприятие")]
    ]
    keyboard = ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)
    return keyboard


def get_events_keyboard():
    """Клавиатура с выбором мероприятия"""
    events = [
        "Space-talks",
        "Ярмарка и запуск ракет",
        "Квиз",
        "Концерт ТьМЫ",
        "Галактик",
        "Презентация кафедр"
    ]
    buttons = [[KeyboardButton(text=event)] for event in events]
    keyboard = ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)
    return keyboard


def get_contact_keyboard():
    """Клавиатура для отправки контакта"""
    button = KeyboardButton(text="📱 Отправить телефон", request_contact=True)
    keyboard = ReplyKeyboardMarkup(keyboard=[[button]], resize_keyboard=True)
    return keyboard


def get_confirm_keyboard(with_change=True):
    """Клавиатура подтверждения с опцией изменения данных"""
    buttons = [
        [KeyboardButton(text="✅ Да, всё верно")],
        [KeyboardButton(text="❌ Нет, заполнить заново")]
    ]
    if with_change:
        buttons.insert(0, [KeyboardButton(text="✏️ Изменить данные")])
    keyboard = ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)
    return keyboard


def get_next_choice_keyboard():
    """Клавиатура после регистрации: ещё мероприятие или завершить"""
    buttons = [
        [KeyboardButton(text="🎫 Зарегистрироваться на другое")],
        [KeyboardButton(text="🚪 Завершить")]
    ]
    keyboard = ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)
    return keyboard


# ---------- Вспомогательные функции ----------
def load_data(file):
    if os.path.exists(file):
        with open(file, "r", encoding="utf-8") as f:
            return json.load(f)
    return {} if file == USERS_FILE else []


def save_data(data, file):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_registrations():
    return load_data(DATA_FILE)


def save_registrations(data):
    save_data(data, DATA_FILE)


def load_users():
    return load_data(USERS_FILE)


def save_users(data):
    save_data(data, USERS_FILE)


def get_user_profile(user_id):
    users = load_users()
    return users.get(str(user_id))


def save_user_profile(user_id, name, contact):
    users = load_users()
    users[str(user_id)] = {"name": name, "contact": contact}
    save_users(users)


def generate_reg_code():
    while True:
        code = secrets.token_hex(3).upper()
        existing = load_registrations()
        if not any(reg.get("reg_code") == code for reg in existing):
            return code


def generate_qr_code(data: str) -> BufferedInputFile:
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    bio = BytesIO()
    img.save(bio, format='PNG')
    bio.seek(0)
    return BufferedInputFile(bio.read(), filename="qr.png")


# ---------- Обработчики ----------
@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Добро пожаловать! Выберите действие:",
        reply_markup=get_main_menu_keyboard()
    )


@dp.message(F.text == "ℹ️ Информация о мероприятиях")
async def info_events(message: types.Message):
    # Замените этот текст на своё описание
    info_text = """
<b>Описание мероприятий:</b>

1. <b>Space-talks</b> — 
2. <b>Ярмарка и запуск ракет</b> — 
3. <b>Квиз</b> — 
4. <b>Концерт ТьМЫ</b> — 
5. <b>Галактик</b> — 
6. <b>Презентация кафедр</b> — 

Подробности можно уточнить у организаторов.
"""
    await message.answer(info_text, parse_mode="HTML", reply_markup=get_main_menu_keyboard())


@dp.message(F.text == "📝 Зарегистрироваться на мероприятие")
async def start_registration(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Выберите мероприятие, на которое хотите записаться:",
        reply_markup=get_events_keyboard()
    )
    await state.set_state(Registration.event)


@dp.message(Registration.event, F.text.in_([
    "Space-talks", "Ярмарка и запуск ракет", "Квиз",
    "Концерт ТьМЫ", "Галактик", "Презентация кафедр"
]))
async def process_event(message: types.Message, state: FSMContext):
    await state.update_data(event=message.text)

    user_id = message.from_user.id
    profile = get_user_profile(user_id)

    if profile:
        await state.update_data(name=profile["name"], contact=profile["contact"])
        await show_summary(message, state, with_change=True)
    else:
        await message.answer(
            "Отлично! Теперь напишите ваше имя и фамилию:",
            reply_markup=ReplyKeyboardRemove()
        )
        await state.set_state(Registration.name)


@dp.message(Registration.event)
async def process_event_invalid(message: types.Message):
    await message.answer(
        "Пожалуйста, выберите мероприятие из списка, используя кнопки ниже.",
        reply_markup=get_events_keyboard()
    )


@dp.message(Registration.name)
async def process_name(message: types.Message, state: FSMContext):
    name = message.text.strip()
    if len(name) < 2:
        await message.answer("Имя должно содержать хотя бы 2 символа. Попробуйте ещё раз:")
        return
    await state.update_data(name=name)
    await message.answer(
        "Теперь поделитесь контактом (нажмите кнопку ниже) или введите номер телефона вручную в формате +71234567890:",
        reply_markup=get_contact_keyboard()
    )
    await state.set_state(Registration.contact)


@dp.message(Registration.contact, F.contact)
async def process_contact_shared(message: types.Message, state: FSMContext):
    phone = message.contact.phone_number
    if not phone.startswith('+'):
        phone = '+' + phone
    await state.update_data(contact=phone)
    await show_summary(message, state, with_change=True)


@dp.message(Registration.contact, F.text)
async def process_contact_manual(message: types.Message, state: FSMContext):
    phone = message.text.strip()
    cleaned = ''.join(c for c in phone if c.isdigit() or c == '+')
    if not cleaned.startswith('+') or not cleaned[1:].isdigit():
        await message.answer(
            "Пожалуйста, введите номер в формате +71234567890 (можно использовать пробелы или дефисы).")
        return
    await state.update_data(contact=cleaned)
    await show_summary(message, state, with_change=True)


async def show_summary(message: types.Message, state: FSMContext, with_change=False):
    data = await state.get_data()
    text = (
        f"Проверьте данные:\n\n"
        f"Мероприятие: {data['event']}\n"
        f"Имя: {data['name']}\n"
        f"Контакт: {data['contact']}\n\n"
        f"Всё верно?"
    )
    await message.answer(text, reply_markup=get_confirm_keyboard(with_change=with_change))
    await state.set_state(Registration.confirm)


@dp.message(Registration.confirm, F.text == "✏️ Изменить данные")
async def process_change_data(message: types.Message, state: FSMContext):
    await message.answer(
        "Введите новое имя и фамилию:",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(Registration.change_name)


@dp.message(Registration.change_name)
async def process_change_name(message: types.Message, state: FSMContext):
    name = message.text.strip()
    if len(name) < 2:
        await message.answer("Имя должно содержать хотя бы 2 символа. Попробуйте ещё раз:")
        return
    await state.update_data(name=name)
    await message.answer(
        "Теперь введите новый номер телефона (или отправьте контакт):",
        reply_markup=get_contact_keyboard()
    )
    await state.set_state(Registration.change_contact)


@dp.message(Registration.change_contact, F.contact)
async def process_change_contact_shared(message: types.Message, state: FSMContext):
    phone = message.contact.phone_number
    if not phone.startswith('+'):
        phone = '+' + phone
    await state.update_data(contact=phone)
    await show_summary(message, state, with_change=True)


@dp.message(Registration.change_contact, F.text)
async def process_change_contact_manual(message: types.Message, state: FSMContext):
    phone = message.text.strip()
    cleaned = ''.join(c for c in phone if c.isdigit() or c == '+')
    if not cleaned.startswith('+') or not cleaned[1:].isdigit():
        await message.answer(
            "Пожалуйста, введите номер в формате +71234567890 (можно использовать пробелы или дефисы).")
        return
    await state.update_data(contact=cleaned)
    await show_summary(message, state, with_change=True)


@dp.message(Registration.confirm, F.text.lower().in_(["✅ да, всё верно", "да"]))
async def process_confirm_yes(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    user_id = message.from_user.id
    reg_code = generate_reg_code()

    all_regs = load_registrations()
    new_reg = {
        "user_id": user_id,
        "username": message.from_user.username,
        "event": user_data["event"],
        "name": user_data["name"],
        "contact": user_data["contact"],
        "reg_code": reg_code,
        "registered_at": datetime.now().isoformat()
    }
    all_regs.append(new_reg)
    save_registrations(all_regs)

    save_user_profile(user_id, user_data["name"], user_data["contact"])

    qr_data = f"Мероприятие: {user_data['event']}\nКод: {reg_code}"
    qr_file = generate_qr_code(qr_data)

    await message.answer_photo(
        photo=qr_file,
        caption=(
            f"✅ Вы успешно зарегистрированы на мероприятие <b>{user_data['event']}</b>!\n\n"
            f"<b>Ваш код подтверждения:</b> <code>{reg_code}</code>\n\n"
            f"Сохраните этот QR-код — он понадобится для входа.\n\n"
            f"Хотите зарегистрироваться на другое мероприятие?"
        ),
        parse_mode="HTML",
        reply_markup=get_next_choice_keyboard()
    )
    await state.set_state(Registration.choose_next)


@dp.message(Registration.confirm, F.text.lower().in_(["❌ нет, заполнить заново", "нет"]))
async def process_confirm_no(message: types.Message, state: FSMContext):
    await message.answer(
        "Хорошо, давайте начнём сначала. Выберите мероприятие:",
        reply_markup=get_events_keyboard()
    )
    await state.set_state(Registration.event)


@dp.message(Registration.choose_next, F.text == "🎫 Зарегистрироваться на другое")
async def choose_next_yes(message: types.Message, state: FSMContext):
    await message.answer(
        "Выберите следующее мероприятие:",
        reply_markup=get_events_keyboard()
    )
    await state.clear()
    await state.set_state(Registration.event)


@dp.message(Registration.choose_next, F.text == "🚪 Завершить")
async def choose_next_no(message: types.Message, state: FSMContext):
    await message.answer(
        "Спасибо за регистрацию! Возвращайтесь ещё.",
        reply_markup=get_main_menu_keyboard()
    )
    await state.clear()


@dp.message(Registration.choose_next)
async def choose_next_invalid(message: types.Message):
    await message.answer(
        "Пожалуйста, выберите действие с помощью кнопок ниже.",
        reply_markup=get_next_choice_keyboard()
    )


@dp.message(Command("cancel"))
async def cmd_cancel(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        await message.answer("Нет активной регистрации.")
        return
    await state.clear()
    await message.answer(
        "Регистрация отменена. Выберите действие:",
        reply_markup=get_main_menu_keyboard()
    )


# ---------- Админ-команда ----------
@dp.message(Command("admin"))
async def cmd_admin(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("У вас нет прав администратора.")
        return

    data = load_registrations()
    if not data:
        await message.answer("Пока никто не зарегистрировался.")
        return

    events_summary = {}
    for reg in data:
        event = reg['event']
        events_summary.setdefault(event, []).append(reg)

    text = "📋 <b>Список зарегистрированных:</b>\n\n"
    for event, regs in events_summary.items():
        text += f"<b>{event}</b> — {len(regs)} чел.\n"
        for i, reg in enumerate(regs, 1):
            username = f"@{reg['username']}" if reg['username'] else "нет"
            text += f"{i}. {reg['name']} — {reg['contact']} ({username}) — код: <code>{reg['reg_code']}</code>\n"
        text += "\n"

    if len(text) > 4000:
        for x in range(0, len(text), 4000):
            await message.answer(text[x:x + 4000], parse_mode="HTML")
    else:
        await message.answer(text, parse_mode="HTML")


# ---------- Запуск бота ----------
async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())