from aiogram.fsm.state import State, StatesGroup


class ImageState(StatesGroup):
    prompt = State()