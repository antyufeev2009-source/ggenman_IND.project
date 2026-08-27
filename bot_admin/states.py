from aiogram.fsm.state import State, StatesGroup

# Хранит состояния для процесса регистрации пользователя
class RegState(StatesGroup):
    waiting_fio = State()
    waiting_phone = State()

# Хранит состояния для процесса заполнения данных о новой вакансии
class VacancyState(StatesGroup):
    company_name = State()
    title = State()
    address = State()
    salary = State()
    duties = State()
    conditions = State()
    requirements = State()
    waiting_public = State()