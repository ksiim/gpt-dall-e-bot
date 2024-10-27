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
            photo=
            image,
            caption=prompt
        )
    else:
        await updating_message.edit_text(
            text="Превышен лимит запросов",
            reply_markup=buy_premium_markup
        )
    await state.clear()
    
@dp.message(F.text)
async def proccess_text_query(message: Message, state: FSMContext):
    user = await Orm.get_user_by_telegram_id(message.from_user.id)
    query = message.text
    
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