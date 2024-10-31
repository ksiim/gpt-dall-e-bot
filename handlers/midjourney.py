from operator import call
import os
import stat
from aiogram import F
from aiogram.filters.command import Command
from aiogram.types import (
    Message, CallbackQuery, FSInputFile
)
from aiogram.fsm.context import FSMContext

from bot import dp, bot

from models.dbs.orm import Orm

from utils.midjourney import MidJourney
from .markups import *


@dp.message(F.photo)
async def describe_image(message: Message):
    photo = message.photo[-1]
    
    file_path = f"images/{message.from_user.id}.jpg"
    image_save_location = os.path.join(os.getcwd(), file_path)
    downloaded_file = await bot.download(photo.file_id, image_save_location)
    file_url = f"http://193.23.118.126:8000/{file_path}"
    
    midjourney = MidJourney(message.from_user.id)
    hash = await midjourney.describe_image(file_url)
    if hash:
        await asyncio.gather(
            Orm.add_midjourney_task(
                telegram_id=message.from_user.id,
                task_hash=hash, prompt=None, type_='describe'
                ),
            prompt_taken_message(message),
            process_midjourney_describe_progress(message, hash, first=True, method='describe', file_path=file_path)
        )
    
    
async def process_midjourney_describe_progress(message: Message, hash: str, method='describe', first=False, file_path=None):
    midjourney = MidJourney(message.from_user.id)
    status, progress, description = await midjourney.check_image_description(hash)
    
    await Orm.update_midjourney_task(
        task_hash=hash,
        status=status,
        progress=progress,
        result=description
    )
    print(status, progress, description)
    
    if status in ["progress", "waiting", "sent", "queued"]:
        await asyncio.sleep(10)
        await process_midjourney_describe_progress(message, hash, method, file_path=file_path)
        
    elif status == "done":
        await message.answer(description)
        await Orm.update_midjourney_task(
            task_hash=hash,
            status='done',
            progress=100,
            result=description
        )
        await midjourney.delete_image(description)

@dp.message(Command('mj'))
async def process_midjourney_prompt(message: Message):
    try:
        prompt = message.text.split(" ", 1)[1]
    except Exception:
        await message.answer(
            text="Напишите /mj и описание изображения"
        )
        return
    
    midjourney = MidJourney(message.from_user.id)
    hash = await midjourney.generate_image(prompt)
    if hash:
        await asyncio.gather(
            Orm.add_midjourney_task(
                telegram_id=message.from_user.id,
                task_hash=hash, prompt=prompt, type_='imagine'
                ),
            prompt_taken_message(message),
            process_midjourney_image_progress(message, hash, first=True)
        )
    else:
        await message.answer(
            text=exception_on_midjourney_text,
        )
        
async def prompt_taken_message(message: Message):
    await message.answer(prompt_taken_message_text)
        
async def process_midjourney_image_progress(message: Message, hash: str, method='imagine', first=False):  
    midjourney = MidJourney(message.from_user.id)
    status, progress, url = await midjourney.check_image_url(hash)
    
    await Orm.update_midjourney_task(
        task_hash=hash,
        status=status,
        progress=progress,
        result=url
    )
    
    if status in ["progress", "waiting", "sent", "queued"]:
        await asyncio.sleep(10)
        await process_midjourney_image_progress(message, hash, method)
        
    elif status == "done":
        
        file_name = await midjourney.save_image(url)
        photo = FSInputFile(file_name)
        
        keyboard = await generate_midjourney_markup(
            hash=hash,
        ) if method in ['imagine', 'variation', 'reroll'] else None
        
        await asyncio.gather(
            message.answer_photo(
                photo=photo,
                reply_markup=keyboard
            ),
            midjourney.delete_image(file_name)
        )
        
@dp.callback_query(lambda callback: callback.data.startswith("variation:"))
async def variation_callback(callback: CallbackQuery):
        
    _, hash, choice = callback.data.split(":")
    
    midjourney = MidJourney(callback.from_user.id)
    hash = await midjourney.variation(hash, choice)
    
    if hash:
        await asyncio.gather(
            prompt_taken_message(callback.message),
            Orm.add_midjourney_task(
                telegram_id=callback.from_user.id,
                task_hash=hash,
                type_='variation'
            ),
            process_midjourney_image_progress(callback.message, hash, 'variation', first=True)
        )
    else:
        await callback.message.answer(exception_on_midjourney_text)
        
@dp.callback_query(lambda callback: callback.data.startswith("upscale:"))
async def upscale_callback(callback: CallbackQuery):
    
    _, hash, choice = callback.data.split(":")
    
    midjourney = MidJourney(callback.from_user.id)
    hash = await midjourney.upscale(hash, choice)
    
    if hash:
        await Orm.add_midjourney_task(
            telegram_id=callback.from_user.id,
            task_hash=hash,
            type_='upscale'
        )
        await process_midjourney_image_progress(callback.message, hash, 'upscale', first=True)
    else:
        await callback.message.answer(exception_on_midjourney_text)
        
@dp.callback_query(lambda callback: callback.data.startswith("reroll:"))
async def reroll_callback(callback: CallbackQuery):
    
    _, hash = callback.data.split(":")
    
    midjourney = MidJourney(callback.from_user.id)
    hash = await midjourney.reroll(hash)
    
    if hash:
        await prompt_taken_message(callback.message)
        await Orm.add_midjourney_task(
            telegram_id=callback.from_user.id,
            task_hash=hash,
            type_='reroll'
        )
        await process_midjourney_image_progress(callback.message, hash, 'reroll', first=True)
    else:
        await callback.message.answer(exception_on_midjourney_text)
        