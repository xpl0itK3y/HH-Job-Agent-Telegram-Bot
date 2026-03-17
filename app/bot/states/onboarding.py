from aiogram.fsm.state import State, StatesGroup


class OnboardingFlow(StatesGroup):
    waiting_for_resume_text = State()
    waiting_for_resume_file = State()
    waiting_for_resume_link = State()
