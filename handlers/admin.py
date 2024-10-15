from bot import dp, bot

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery
from aiogram.filters.command import Command
from aiogram.fsm.context import FSMContext
from aiogram import F

from models.dbs.models import *

from .callbacks import *
from .markups import *
from .states import *
from .filters import *

from .user import *

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