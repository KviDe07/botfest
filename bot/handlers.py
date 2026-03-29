import html
from datetime import datetime

from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import FSInputFile, LinkPreviewOptions

from .config import ADMIN_IDS, REGISTRATION_EVENTS, EXTERNAL_REGISTRATIONS, EVENT_DESCRIPTIONS
from .keyboards import (
    BACK_BUTTON_TEXT,
    main_menu_keyboard,
    events_keyboard,
    events_info_keyboard,
    name_input_keyboard,
    contact_keyboard,
    contact_keyboard_with_back,
    confirm_keyboard,
    next_choice_keyboard,
)
from .states import Registration
from .storage import (
    load_registrations,
    save_registrations,
    get_user_profile,
    save_user_profile,
)
from .utils import generate_reg_code, generate_qr, normalize_phone

router = Router()


# ---------- /start ----------

@router.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Добро пожаловать! Выберите действие:", reply_markup=main_menu_keyboard())


# ---------- /cancel ----------

@router.message(Command("cancel"))
async def cmd_cancel(message: types.Message, state: FSMContext) -> None:
    if await state.get_state() is None:
        await message.answer("Нет активной регистрации.")
        return
    await state.clear()
    await message.answer("Регистрация отменена. Выберите действие:", reply_markup=main_menu_keyboard())


# ---------- Расписание ----------

@router.message(F.text == "📅 Расписание мероприятий")
async def schedule_events(message: types.Message) -> None:
    import os
    photo_path = "media/schedule.jpg"
    if os.path.exists(photo_path):
        photo = FSInputFile(photo_path)
        await message.answer_photo(photo=photo, caption="Расписание мероприятий Фестиваля космонавтики", reply_markup=main_menu_keyboard())
    else:
        await message.answer("Фото с расписанием пока не загружено.", reply_markup=main_menu_keyboard())


# ---------- Информация ----------

@router.message(F.text == "ℹ️ Информация о мероприятиях")
async def info_events(message: types.Message) -> None:
    await message.answer(
        "Выберите мероприятие, чтобы узнать о нем подробнее:", 
        reply_markup=events_info_keyboard()
    )

@router.callback_query(F.data.startswith("info_"))
async def process_info_callback(callback: types.CallbackQuery) -> None:
    event_name = callback.data[5:]
    
    if event_name in EVENT_DESCRIPTIONS:
        desc = EVENT_DESCRIPTIONS[event_name]
        await callback.message.answer(
            desc, 
            parse_mode="HTML", 
            link_preview_options=LinkPreviewOptions(is_disabled=True)
        )
    else:
        await callback.message.answer("К сожалению, описание для этого мероприятия пока не добавлено.")
        
    await callback.answer()


# ---------- Регистрация: старт ----------

@router.message(F.text == "📝 Зарегистрироваться на мероприятие")
async def start_registration(message: types.Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Выберите мероприятие, на которое хотите записаться:", reply_markup=events_keyboard())
    await state.set_state(Registration.event)


@router.message(Registration.event, F.text == BACK_BUTTON_TEXT)
async def registration_back_from_events(message: types.Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Выберите действие:", reply_markup=main_menu_keyboard())


@router.message(Registration.event, F.text.in_(REGISTRATION_EVENTS))
async def process_event(message: types.Message, state: FSMContext) -> None:
    event_name = message.text
    
    if event_name in EXTERNAL_REGISTRATIONS:
        url = EXTERNAL_REGISTRATIONS[event_name]
        await message.answer(
            f"Для мероприятия <b>{event_name}</b> предусмотрена внешняя регистрация.\n\n"
            f"Пожалуйста, зарегистрируйтесь по ссылке: {url}",
            parse_mode="HTML",
            reply_markup=main_menu_keyboard()
        )
        await state.clear()
        return

    await state.update_data(event=event_name)
    profile = get_user_profile(message.from_user.id)
    if profile:
        await state.update_data(name=profile["name"], contact=profile["contact"])
        await _show_summary(message, state, with_change=True)
    else:
        await message.answer(
            "Отлично! Введите фамилию, имя и отчество:",
            reply_markup=name_input_keyboard(),
        )
        await state.set_state(Registration.name)


@router.message(Registration.event)
async def process_event_invalid(message: types.Message) -> None:
    await message.answer(
        "Пожалуйста, выберите мероприятие из списка или нажмите «Назад».",
        reply_markup=events_keyboard(),
    )


# ---------- ФИО ----------

@router.message(Registration.name, F.text == BACK_BUTTON_TEXT)
async def registration_back_from_name(message: types.Message, state: FSMContext) -> None:
    await message.answer("Выберите мероприятие, на которое хотите записаться:", reply_markup=events_keyboard())
    await state.set_state(Registration.event)


@router.message(Registration.name)
async def process_name(message: types.Message, state: FSMContext) -> None:
    if not message.text:
        await message.answer("Пожалуйста, отправьте текст — фамилию, имя и отчество.")
        return
    name = message.text.strip()
    if len(name) < 2:
        await message.answer("ФИО должно содержать хотя бы 2 символа. Попробуйте ещё раз:")
        return
    await state.update_data(name=name)
    await message.answer(
        "Теперь поделитесь контактом (нажмите кнопку ниже) или введите номер телефона вручную в формате +71234567890:",
        reply_markup=contact_keyboard_with_back(),
    )
    await state.set_state(Registration.contact)


# ---------- Контакт ----------

@router.message(Registration.contact, F.text == BACK_BUTTON_TEXT)
async def registration_back_from_contact(message: types.Message, state: FSMContext) -> None:
    await message.answer(
        "Введите фамилию, имя и отчество:",
        reply_markup=name_input_keyboard(),
    )
    await state.set_state(Registration.name)


@router.message(Registration.contact, F.contact)
async def process_contact_shared(message: types.Message, state: FSMContext) -> None:
    phone = message.contact.phone_number
    if not phone.startswith("+"):
        phone = "+" + phone
    await state.update_data(contact=phone)
    await _show_summary(message, state, with_change=True)


@router.message(Registration.contact, F.text)
async def process_contact_manual(message: types.Message, state: FSMContext) -> None:
    phone = normalize_phone(message.text.strip())
    if phone is None:
        await message.answer(
            "Пожалуйста, введите номер в формате +71234567890 (можно использовать пробелы или дефисы) или нажмите «Назад».",
            reply_markup=contact_keyboard_with_back(),
        )
        return
    await state.update_data(contact=phone)
    await _show_summary(message, state, with_change=True)


@router.message(Registration.contact)
async def process_contact_other(message: types.Message) -> None:
    await message.answer(
        "Отправьте номер текстом в формате +71234567890, нажмите «📱 Отправить телефон» или «Назад».",
        reply_markup=contact_keyboard_with_back(),
    )


# ---------- Изменение данных ----------

@router.message(Registration.confirm, F.text == "✏️ Изменить данные")
async def process_change_data(message: types.Message, state: FSMContext) -> None:
    await message.answer(
        "Введите фамилию, имя и отчество заново:",
        reply_markup=name_input_keyboard(),
    )
    await state.set_state(Registration.change_name)


@router.message(Registration.change_name, F.text == BACK_BUTTON_TEXT)
async def registration_back_from_change_name(message: types.Message, state: FSMContext) -> None:
    await _show_summary(message, state, with_change=True)


@router.message(Registration.change_name)
async def process_change_name(message: types.Message, state: FSMContext) -> None:
    if not message.text:
        await message.answer("Пожалуйста, отправьте текст — фамилию, имя и отчество.")
        return
    name = message.text.strip()
    if len(name) < 2:
        await message.answer("ФИО должно содержать хотя бы 2 символа. Попробуйте ещё раз:")
        return
    await state.update_data(name=name)
    await message.answer(
        "Теперь введите новый номер телефона (или отправьте контакт):",
        reply_markup=contact_keyboard_with_back(),
    )
    await state.set_state(Registration.change_contact)


@router.message(Registration.change_contact, F.text == BACK_BUTTON_TEXT)
async def registration_back_from_change_contact(message: types.Message, state: FSMContext) -> None:
    await message.answer(
        "Введите фамилию, имя и отчество:",
        reply_markup=name_input_keyboard(),
    )
    await state.set_state(Registration.change_name)


@router.message(Registration.change_contact, F.contact)
async def process_change_contact_shared(message: types.Message, state: FSMContext) -> None:
    phone = message.contact.phone_number
    if not phone.startswith("+"):
        phone = "+" + phone
    await state.update_data(contact=phone)
    await _show_summary(message, state, with_change=True)


@router.message(Registration.change_contact, F.text)
async def process_change_contact_manual(message: types.Message, state: FSMContext) -> None:
    phone = normalize_phone(message.text.strip())
    if phone is None:
        await message.answer(
            "Пожалуйста, введите номер в формате +71234567890 (можно использовать пробелы или дефисы) или нажмите «Назад».",
            reply_markup=contact_keyboard_with_back(),
        )
        return
    await state.update_data(contact=phone)
    await _show_summary(message, state, with_change=True)


@router.message(Registration.change_contact)
async def process_change_contact_other(message: types.Message) -> None:
    await message.answer(
        "Отправьте номер текстом в формате +71234567890, нажмите «📱 Отправить телефон» или «Назад».",
        reply_markup=contact_keyboard_with_back(),
    )


# ---------- Подтверждение ----------

async def _show_summary(message: types.Message, state: FSMContext, with_change: bool = False) -> None:
    data = await state.get_data()
    try:
        event, name, contact = data["event"], data["name"], data["contact"]
    except KeyError:
        await message.answer("Данные сессии устарели. Начните заново: /start")
        await state.clear()
        return
    text = (
        f"Проверьте данные:\n\n"
        f"Мероприятие: {event}\n"
        f"ФИО: {name}\n"
        f"Контакт: {contact}\n\n"
        f"Всё верно?"
    )
    await message.answer(text, reply_markup=confirm_keyboard(with_change=with_change))
    await state.set_state(Registration.confirm)


@router.message(Registration.confirm, F.text == "✅ Да, всё верно")
async def process_confirm_yes(message: types.Message, state: FSMContext) -> None:
    user_data = await state.get_data()
    if not all(k in user_data for k in ("event", "name", "contact")):
        await message.answer("Данные сессии устарели. Начните заново: /start")
        await state.clear()
        return
    user_id = message.from_user.id
    reg_code = generate_reg_code()

    all_regs = load_registrations()
    all_regs.append({
        "user_id": user_id,
        "username": message.from_user.username,
        "event": user_data["event"],
        "name": user_data["name"],
        "contact": user_data["contact"],
        "reg_code": reg_code,
        "registered_at": datetime.now().isoformat(),
    })
    save_registrations(all_regs)
    save_user_profile(user_id, user_data["name"], user_data["contact"])

    qr_file = generate_qr(f"Мероприятие: {user_data['event']}\nКод: {reg_code}")
    await message.answer_photo(
        photo=qr_file,
        caption=(
            f"✅ Вы успешно зарегистрированы на мероприятие <b>{user_data['event']}</b>!\n\n"
            f"<b>Ваш код подтверждения:</b> <code>{reg_code}</code>\n\n"
            f"Сохраните этот QR-код — он понадобится для входа.\n\n"
            f"Хотите зарегистрироваться на другое мероприятие?"
        ),
        parse_mode="HTML",
        reply_markup=next_choice_keyboard(),
    )
    await state.set_state(Registration.choose_next)


@router.message(Registration.confirm, F.text == "❌ Нет, заполнить заново")
async def process_confirm_no(message: types.Message, state: FSMContext) -> None:
    await message.answer("Хорошо, давайте начнём сначала. Выберите мероприятие:", reply_markup=events_keyboard())
    await state.set_state(Registration.event)


@router.message(Registration.confirm)
async def process_confirm_invalid(message: types.Message) -> None:
    await message.answer("Выберите действие кнопкой ниже.", reply_markup=confirm_keyboard(with_change=True))


# ---------- После регистрации ----------

@router.message(Registration.choose_next, F.text == "🎫 Зарегистрироваться на другое")
async def choose_next_yes(message: types.Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Выберите следующее мероприятие:", reply_markup=events_keyboard())
    await state.set_state(Registration.event)


@router.message(Registration.choose_next, F.text == "🚪 Завершить")
async def choose_next_no(message: types.Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Спасибо за регистрацию! Возвращайтесь ещё.", reply_markup=main_menu_keyboard())


@router.message(Registration.choose_next)
async def choose_next_invalid(message: types.Message) -> None:
    await message.answer("Пожалуйста, выберите действие с помощью кнопок ниже.", reply_markup=next_choice_keyboard())


# ---------- Админ ----------

@router.message(Command("admin"))
async def cmd_admin(message: types.Message) -> None:
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("У вас нет прав администратора.")
        return

    data = load_registrations()
    if not data:
        await message.answer("Пока никто не зарегистрировался.")
        return

    events_summary: dict[str, list] = {}
    for reg in data:
        events_summary.setdefault(reg["event"], []).append(reg)

    text = "📋 <b>Список зарегистрированных:</b>\n\n"
    for event, regs in events_summary.items():
        text += f"<b>{html.escape(str(event))}</b> — {len(regs)} чел.\n"
        for i, reg in enumerate(regs, 1):
            if reg.get("username"):
                username = f"@{html.escape(str(reg['username']))}"
            else:
                username = "нет"
            name = html.escape(str(reg.get("name", "")))
            contact = html.escape(str(reg.get("contact", "")))
            code = html.escape(str(reg.get("reg_code", "")))
            text += f"{i}. {name} — {contact} ({username}) — код: <code>{code}</code>\n"
        text += "\n"

    for chunk in range(0, len(text), 4000):
        await message.answer(text[chunk:chunk + 4000], parse_mode="HTML")
