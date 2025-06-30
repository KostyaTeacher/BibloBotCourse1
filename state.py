from aiogram.fsm.state import State, StatesGroup

class BookForm(StatesGroup):
    name = State()
    description = State()
    rating = State()
    genre = State()
    authors = State()
    poster = State()