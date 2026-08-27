from aiogram.fsm.state import State, StatesGroup

class RegState(StatesGroup):
    full_name = State()
    photo = State()
    birth_date = State()
    phone = State()
    specialization = State()
    desired_jobs = State()
    city = State()
    confirm = State()
