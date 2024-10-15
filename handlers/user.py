from aiogram import F
from aiogram.filters.command import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    Message, CallbackQuery, FSInputFile
)
from aiogram.enums.chat_action import ChatAction

from bot import dp, bot

from models.dbs.orm import Orm
from models.dbs.models import *

from .callbacks import *
from .markups import *
from .states import *
from .filters import *
from .openai_api import OpenAI_API


@dp.message(Command('start'))
async def start_message_handler(message: Message, state: FSMContext):
    await state.clear()
    
    await Orm.create_user(message)
    await send_start_message(message)
    
async def send_start_message(message: Message):
    await bot.send_message(
        chat_id=message.from_user.id,
        text=await generate_start_text(message),
    )
    
@dp.message(Command('help'))
async def help_message_handler(message: Message, state: FSMContext):
    await state.clear()
    
    await message.answer(
        text=help_text,
        reply_markup=close_markup
    )

@dp.callback_query(F.data == 'close')
async def close_callback_handler(callback: CallbackQuery):
    await callback.message.delete()
    
@dp.message(Command('profile'))
async def profile_message_handler(message: Message, state: FSMContext):
    await state.clear()
    
    user = await Orm.get_user_by_telegram_id(message.from_user.id)

    await message.answer(
        text=await generate_profile_text(user),
        reply_markup=close_markup
    )
    
@dp.message(Command("model"))
async def change_model_command(message: Message, state: FSMContext):
    await state.clear()
    
    user = await Orm.get_user_by_telegram_id(message.from_user.id)
    await message.answer(
        text=await generate_current_models_text(user),
        reply_markup=await generate_model_markup(user)
    )
    
@dp.message(Command("premium"))
async def premium_command(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        text=rates_info_text,
        reply_markup=buy_premium_markup
    )
    
@dp.callback_query(F.data.startswith("change_to"))
async def change_chat_model(callback: CallbackQuery):
    model = callback.data.split(":")[-1]
    user = await Orm.get_user_by_telegram_id(callback.from_user.id)
    user = await Orm.update_chat_model(user, model)
    await callback.message.edit_text(
        text=await generate_current_models_text(user),
        reply_markup=await generate_model_markup(user)
    )

@dp.message(Command("reset"))
async def reset_context_command(message: Message, state: FSMContext):
    await state.clear()
    
    user = await Orm.get_user_by_telegram_id(message.from_user.id)
    await Orm.clear_context_messages(user.id)
    await message.answer(
        text="Контекст диалога очищен"
    )

async def send_statistic_message(telegram_id):
    await bot.send_message(
        chat_id=telegram_id,
        text=await generate_statistic_text()
    )

@dp.message(Command('stat'), IsAdmin())
async def statistic_handler(message: Message):
    await send_statistic_message(
        telegram_id=message.from_user.id,
    )
    
@dp.message(Command("img"))
async def image_command(message: Message, state: FSMContext):
    await state.clear()
    
    user = await Orm.get_user_by_telegram_id(message.from_user.id)
    prompt = message.text.split(" ", 1)[1]
    
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
    
    answer = await open_ai(query)
    
    if answer:
        await updating_message.delete()
        
        await message.answer(
            text=answer
        )
    else:
        await updating_message.edit_text(
            text="Превышен лимит запросов",
            reply_markup=buy_premium_markup
        )