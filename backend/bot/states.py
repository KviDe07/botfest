from aiogram.fsm.state import State, StatesGroup


class Registration(StatesGroup):
    event = State()
    name = State()
    contact = State()
    confirm = State()
    choose_next = State()
    change_name = State()
    change_contact = State()
