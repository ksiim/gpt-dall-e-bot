
from aiogram.types import Message 
from aiogram.filters.command import Command
from aiogram.fsm.context import FSMContext
from aiogram import F

from bot import dp, bot

from models.dbs.models import *

from .callbacks import *
from .markups import *
from .states import *
from .filters import *


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
    