from aiogram.fsm.state import State, StatesGroup

class ProfileStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_email = State()
    waiting_for_organization = State()
    waiting_for_social = State()

class RegistrationStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_organization = State()
    waiting_for_social = State()

class CommandStates(StatesGroup):
    waiting_for_command = State()
    waiting_for_tag = State()
    waiting_for_voice = State() 