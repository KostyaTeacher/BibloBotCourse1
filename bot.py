import asyncio
import logging
import sys
import json

from aiogram.fsm.context import FSMContext

from config import BOT_TOKEN
from commands import (START_BOT_COMMAND, BOOKS_BOT_COMMAND, BOOKS_BOT_CREATE_COMMAND,
                      BOOKS_COMMAND, BOOKS_CREATE_COMMAND)
from aiogram import Bot, Dispatcher, html
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery, URLInputFile, ReplyKeyboardRemove
from keyboards import books_keyboard_markup, BookCallback
from model import Book
from state import BookForm

# Bot token can be obtained via https://t.me/BotFather


# All handlers should be attached to the Router (or Dispatcher)

dp = Dispatcher()


@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    logging.info(f"User {message.from_user.full_name} push command start")
    await message.answer(f"Вітаю, {html.bold(message.from_user.full_name)}! \n"
                         "Я бот для управління бібліотекою книг")


def get_books(file_path: str = "data.json", book_id: int | None = None) -> list[dict] | dict:
    with open(file_path, "r", encoding="utf-8") as fp:
        books = json.load(fp)
        if book_id != None and book_id < len(books):
            return books[book_id]
        return books

def add_book(
   book: dict,
   file_path: str = "data.json",
):
   books = get_books(file_path=file_path, book_id=None)
   if books:
       books.append(book)
       with open(file_path, "w", encoding="utf-8") as fp:
           json.dump(
               books,
               fp,
               indent=4,
               ensure_ascii=False,
           )


@dp.message(BOOKS_COMMAND)
async def books(message: Message) -> None:
    data = get_books()
    markup = books_keyboard_markup(book_list=data)
    await message.answer(f"Список книг. Натисніть на назву для деталей.",
                         reply_markup=markup)

@dp.callback_query(BookCallback.filter())
async def callback_book(callback: CallbackQuery, callback_data: BookCallback) -> None:
    print(callback)
    print(callback_data)

    book_id = callback_data.id
    book_data = get_books(book_id=book_id)
    book = Book(**book_data)

    text = f"Книга: {book.name}\n" \
           f"Опис: {book.description}\n" \
           f"Рейтинг: {book.rating}\n" \
           f"Жанр: {book.genre}\n" \
           f"Автори: {','.join(book.authors)}\n"

    try:
        await callback.message.answer_photo(
            caption=text,
            photo=URLInputFile(
                book.poster,
                filename=f"{book.name}_cover.{book.poster.split('.')[-1]}"
            )
        )
    except Exception as e:
        # If image loading fails, send just the text
        await callback.message.answer(text)
        logging.error(f"Failed to load image for book {book.name}: {str(e)}")


@dp.message(BOOKS_CREATE_COMMAND)
async def book_create(message: Message, state: FSMContext) -> None:
    await state.set_state(BookForm.name)
    await message.answer(f"Введіть назву книги.", reply_markup=ReplyKeyboardRemove())

@dp.message(BookForm.name)
async def book_name(message: Message, state: FSMContext) -> None:
    await state.update_data(name=message.text)
    await state.set_state(BookForm.description)
    await message.answer(f"Введіть опис книги.", reply_markup=ReplyKeyboardRemove())

@dp.message(BookForm.description)
async def book_description(message: Message, state: FSMContext) -> None:
    await state.update_data(description=message.text)
    await state.set_state(BookForm.rating)
    await message.answer(f"Введіть рейтинг книги від 0 до 10.", reply_markup=ReplyKeyboardRemove())

@dp.message(BookForm.rating)
async def book_rating(message: Message, state: FSMContext) -> None:
    await state.update_data(rating=message.text)
    await state.set_state(BookForm.genre)
    await message.answer(f"Введіть жанр книги.", reply_markup=ReplyKeyboardRemove())

@dp.message(BookForm.genre)
async def book_genre(message: Message, state: FSMContext) -> None:
    await state.update_data(genre=message.text)
    await state.set_state(BookForm.authors)
    await message.answer(f"Введіть авторів книги.\n" + html.bold("Обов'язкова кома та відступ після неї"),
                         reply_markup=ReplyKeyboardRemove())

@dp.message(BookForm.authors)
async def book_authors(message: Message, state: FSMContext) -> None:
    await state.update_data(authors=[x for x in message.text.split(", ")])
    await state.set_state(BookForm.poster)
    await message.answer(f"Введіть посилання на обкладинку книги.", reply_markup=ReplyKeyboardRemove())

@dp.message(BookForm.poster)
async def book_poster(message: Message, state: FSMContext) -> None:
   data = await state.update_data(poster=message.text)
   book = Book(**data)
   add_book(book.model_dump())
   await state.clear()
   await message.answer(
       f"Книгу {book.name} успішно додано!",
       reply_markup=ReplyKeyboardRemove(),
   )


async def main() -> None:
    # Initialize Bot instance with default bot properties which will be passed to all API calls
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

    await bot.set_my_commands(
        [
            START_BOT_COMMAND,
            BOOKS_BOT_COMMAND,
            BOOKS_BOT_CREATE_COMMAND
        ]
    )

    # And the run events dispatching
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())