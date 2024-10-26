import stat
from aiogram import F
from aiogram.filters.command import Command
from aiogram.types import (
    Message, CallbackQuery, FSInputFile
)
from aiogram.fsm.context import FSMContext
from aiogram.enums.chat_action import ChatAction

from bot import dp, bot

from models.dbs.orm import Orm

from utils import midjourney
from utils.midjourney import MidJourney
from .markups import *


@dp.message(Command('mj'))
async def process_midjourney_prompt(message: Message):
    prompt = message.text.split(' ', 1)[1]
    midjourney = MidJourney()
    hash = await midjourney.generate_image(prompt)
    if hash:
        await Orm.add_midjourney_task(
            telegram_id=message.from_user.id,
            task_hash=hash,
            prompt=prompt,
            type_='imagine'
        )
        await prompt_taken_message(message)
        await process_midjourney_progress(message, hash, first=True)
    else:
        await message.answer("Ошибка создания задачи")
        
async def prompt_taken_message(message: Message):
    await message.answer(prompt_taken_message_text)
        
async def process_midjourney_progress(message: Message, hash: str, method='imagine', first=False):  
    midjourney = MidJourney()
    status, progress, url = await midjourney.check_image_url(hash)
    
    await Orm.update_midjourney_task(
        task_hash=hash,
        status=status,
        progress=progress,
        result=url
    )
    
    if status == "progress" or status == "waiting" or status == "sent":
        await asyncio.sleep(5)
        await process_midjourney_progress(message, hash, method)
        
    elif status == "done":
        file_name = await midjourney.save_image(url)
        photo = FSInputFile(file_name)
        
        keyboard = await generate_midjourney_markup(
            hash=hash,
        ) if method in ['imagine', 'variation', 'reroll'] else None
        
        await message.answer_photo(
            photo=photo,
            reply_markup=keyboard
        )
        await midjourney.delete_image(file_name)
        
@dp.callback_query(lambda callback: callback.data.startswith("variation:"))
async def variation_callback(callback: CallbackQuery):
    await prompt_taken_message(callback.message)
        
    _, hash, choice = callback.data.split(":")
    
    midjourney = MidJourney()
    hash = await midjourney.variation(hash, choice)
    
    if hash:
        await Orm.add_midjourney_task(
            telegram_id=callback.from_user.id,
            task_hash=hash,
            type_='variation'
        )
        await process_midjourney_progress(callback.message, hash, 'variation', first=True)
    else:
        await callback.message.answer("Ошибка создания задачи")
        
@dp.callback_query(lambda callback: callback.data.startswith("upscale:"))
async def upscale_callback(callback: CallbackQuery):
    
    _, hash, choice = callback.data.split(":")
    
    midjourney = MidJourney()
    hash = await midjourney.upscale(hash, choice)
    
    if hash:
        await Orm.add_midjourney_task(
            telegram_id=callback.from_user.id,
            task_hash=hash,
            type_='upscale'
        )
        await process_midjourney_progress(callback.message, hash, 'upscale', first=True)
    else:
        await callback.message.answer("Ошибка создания задачи")
        
@dp.callback_query(lambda callback: callback.data.startswith("reroll:"))
async def reroll_callback(callback: CallbackQuery):
    await prompt_taken_message(callback.message)
    
    _, hash = callback.data.split(":")
    
    midjourney = MidJourney()
    hash = await midjourney.reroll(hash)
    
    if hash:
        await Orm.add_midjourney_task(
            telegram_id=callback.from_user.id,
            task_hash=hash,
            type_='reroll'
        )
        await process_midjourney_progress(callback.message, hash, 'reroll', first=True)
    else:
        await callback.message.answer("Ошибка создания задачи")
        