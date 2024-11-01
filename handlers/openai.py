from io import BytesIO
import os
import aiofiles
from aiogram import F
from aiogram.filters.command import Command
from aiogram.types import (
    Message
)
from aiogram.fsm.context import FSMContext
from aiogram.enums.chat_action import ChatAction

from bot import dp, bot

from models.dbs.orm import Orm

from utils.openai_api import OpenAI_API
from .markups import *


@dp.message(F.photo)
async def describe_image(message: Message):
    user = await Orm.get_user_by_telegram_id(message.from_user.id)
    if user.rate_id == 1:
        return await message.answer(
            text=describe_image_rate_text,
            reply_markup=buy_premium_markup
        )
    
    image_url, file_path = await download_photo_and_get_image_url(message)
    
    
    updating_message = await message.answer(
        text=waiting_text
    )
    await bot.send_chat_action(message.chat.id, action=ChatAction.TYPING)
    
    openai = OpenAI_API(user=user)
    description = await openai.desribe_image(image_url)
    
    await updating_message.delete()
    
    if description:
        await message.answer(description)
        os.remove(file_path)
    else:
        await message.answer(
            text="Превышен лимит запросов",
            reply_markup=buy_premium_markup
        )

async def download_photo_and_get_image_url(message):
    photo = message.photo[-1]
    file_path = f"images/{message.from_user.id}.jpg"
    image_save_location = os.path.join(os.getcwd(), file_path)
    await bot.download(photo.file_id, image_save_location)
    file_url = f"http://193.23.118.126:8000/image/{file_path}"
    return (file_url, file_path)

@dp.message(Command("dalle"))
async def image_command(message: Message, state: FSMContext):
    await state.clear()

    user = await Orm.get_user_by_telegram_id(message.from_user.id)
    try:
        prompt = message.text.split(" ", 1)[1]
    except Exception:
        await message.answer(
            text="Напишите /dalle и описание изображения"
        )
        return

    updating_message = await message.answer(
        text=waiting_text
    )
    await bot.send_chat_action(message.chat.id, action=ChatAction.TYPING)

    open_ai = OpenAI_API(user=user)

    image = await open_ai.generate_image(prompt)

    if image:
        await updating_message.delete()

        await bot.send_photo(
            chat_id=message.chat.id,
            photo=image,
            caption=prompt
        )
    else:
        await updating_message.edit_text(
            text="Превышен лимит запросов",
            reply_markup=buy_premium_markup
        )
    await state.clear()


async def path_to_bytesio(file_path):
    # Асинхронно открываем файл в бинарном режиме и читаем его содержимое
    async with aiofiles.open(file_path, 'rb') as file:
        file_content = await file.read()

    # Загружаем содержимое в объект BytesIO
    return BytesIO(file_content)


@dp.message(F.voice)
async def audio_query(message: Message, state: FSMContext):
    user = await Orm.get_user_by_telegram_id(message.from_user.id)
    
    if user.rate_id == 1:
        return await message.answer(
            text=voice_rate_text,
            reply_markup=buy_premium_markup
        )
    
    file_path = await download_voice_message(message)

    openai = OpenAI_API(user=user)
    transcription = await openai.get_transcription_from_audio(file_path)

    os.remove(file_path)

    await proccess_text_query(await Orm.get_user_by_telegram_id(message.from_user.id), message, transcription)

async def download_voice_message(message: Message):
    audio_file_id = message.voice.file_id

    file_name = f'voices/{message.from_user.id}.ogg'

    file_path = os.path.join(os.getcwd(), file_name)

    await bot.download(audio_file_id, file_name)
    return file_path


@dp.message(F.text)
async def text_query_handler(message: Message, state: FSMContext):
    user = await Orm.get_user_by_telegram_id(message.from_user.id)
    query = message.text
    await proccess_text_query(user, message, query)
    
async def proccess_text_query(user, message: Message, query):

    updating_message = await message.answer(
        text=waiting_text
    )
    await bot.send_chat_action(message.chat.id, action=ChatAction.TYPING)

    open_ai = OpenAI_API(user=user)

    answers_list = await open_ai(query)

    if answers_list:
        await updating_message.delete()

        for answer in answers_list:
            await message.answer(
                text=answer,
                parse_mode=None

            )
    else:
        await updating_message.edit_text(
            text="Превышен лимит запросов",
            reply_markup=buy_premium_markup
        )
