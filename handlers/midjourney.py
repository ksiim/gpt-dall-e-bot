from aiogram import F
from aiogram.filters.command import Command
from aiogram.types import (
    Message, CallbackQuery
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
            user_id=message.from_user.id,
            task_hash=hash,
            prompt=prompt
        )
        await process_midjourney_progress(message, hash)
    else:
        await message.answer("Ошибка создания задачи")
        
async def process_midjourney_progress(message: Message, hash: str):    
    midjourney = MidJourney()
    status, progress, url = await midjourney.check_image_url(hash)
    
    await Orm.update_midjourney_task(
        task_hash=hash,
        status=status,
        progress=progress,
        result=url
    )
    
    if status == "progress":
        await message.edit_text(f"Прогресс: {progress}%")
        await asyncio.sleep(5)
        await process_midjourney_progress(message, hash)
        
    elif status == "done":
        await message.delete()
        await message.answer_photo(
            text=url,
            reply_markup=await generate_midjourney_markup(
            hash=hash,    
            )
        )
        
@dp.callback_query(lambda callback: callback.data.startswith("variation:"))
async def variation_callback(callback: CallbackQuery):
    await callback.message.delete_reply_markup()
    
    _, hash, choice = callback.data.split(":", 1)[1]
    
    midjourney = MidJourney()
    hash = await midjourney.variation(hash, choice)
    
    if hash:
        await process_midjourney_progress(callback.message, hash)
    else:
        await callback.answer("Ошибка создания задачи")
        
@dp.callback_query(lambda callback: callback.data.startswith("upscale:"))
async def upscale_callback(callback: CallbackQuery):
    await callback.message.delete_reply_markup()
    
    _, hash, choice = callback.data.split(":", 1)[1]
    
    midjourney = MidJourney()
    hash = await midjourney.upscale(hash, choice)
    
    if hash:
        await process_midjourney_progress(callback.message, hash)
    else:
        await callback.answer("Ошибка создания задачи")
        
@dp.callback_query(lambda callback: callback.data.startswith("reroll:"))
async def reroll_callback(callback: CallbackQuery):
    await callback.message.delete_reply_markup()
    
    _, hash = callback.data.split(":", 1)[1]
    
    midjourney = MidJourney()
    hash = await midjourney.reroll(hash)
    
    if hash:
        await process_midjourney_progress(callback.message, hash)
    else:
        await callback.answer("Ошибка создания задачи")