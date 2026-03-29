from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

from .config import EVENTS, REGISTRATION_EVENTS

BACK_BUTTON_TEXT = "◀️ Назад"
MY_REGISTRATIONS_TEXT = "📋 Мои регистрации"


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    buttons = [
        [KeyboardButton(text="📅 Расписание мероприятий")],
        [KeyboardButton(text="ℹ️ Информация о мероприятиях")],
        [KeyboardButton(text="📝 Зарегистрироваться на мероприятие")],
        [KeyboardButton(text=MY_REGISTRATIONS_TEXT)],
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


def events_keyboard() -> ReplyKeyboardMarkup:
    buttons = [[KeyboardButton(text=event)] for event in REGISTRATION_EVENTS]
    buttons.append([KeyboardButton(text=BACK_BUTTON_TEXT)])
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


def name_input_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=BACK_BUTTON_TEXT)]],
        resize_keyboard=True,
    )


def events_info_keyboard() -> InlineKeyboardMarkup:
    buttons = []
    for i in range(0, len(EVENTS), 2):
        row = [InlineKeyboardButton(text=EVENTS[i], callback_data=f"info_{EVENTS[i]}")]
        if i + 1 < len(EVENTS):
            row.append(InlineKeyboardButton(text=EVENTS[i+1], callback_data=f"info_{EVENTS[i+1]}"))
        buttons.append(row)
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def contact_keyboard() -> ReplyKeyboardMarkup:
    button = KeyboardButton(text="📱 Отправить телефон", request_contact=True)
    return ReplyKeyboardMarkup(keyboard=[[button]], resize_keyboard=True)


def contact_keyboard_with_back() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📱 Отправить телефон", request_contact=True)],
            [KeyboardButton(text=BACK_BUTTON_TEXT)],
        ],
        resize_keyboard=True,
    )


def confirm_keyboard(with_change: bool = True) -> ReplyKeyboardMarkup:
    buttons = [
        [KeyboardButton(text="✅ Да, всё верно")],
        [KeyboardButton(text="❌ Нет, заполнить заново")],
    ]
    if with_change:
        buttons.insert(0, [KeyboardButton(text="✏️ Изменить данные")])
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


def next_choice_keyboard() -> ReplyKeyboardMarkup:
    buttons = [
        [KeyboardButton(text="🎫 Зарегистрироваться на другое")],
        [KeyboardButton(text="🚪 Завершить")],
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)
