from aiogram import F
from aiogram.types import Message, CallbackQuery, PreCheckoutQuery, LabeledPrice

from bot import dp, bot

from config import PAYMENTS_TOKEN

from models.dbs.orm import Orm
from models.dbs.models import *

from .callbacks import *
from .markups import *
from .states import *


@dp.callback_query(F.data == "change_rate")
async def change_rate_handler(callback: CallbackQuery):
    await callback.message.delete_reply_markup()
    
    text = await generate_change_rate_text()

    await callback.message.answer(
        text=text,
        reply_markup=await generate_rates_keyboard(),
    )

@dp.callback_query(lambda callback: callback.data.startswith("buy_rate"))
async def choose_period(callback: CallbackQuery):
    await callback.message.delete_reply_markup()
    
    rate_id = int(callback.data.split(":")[-1])
    
    rate = await Orm.get_rate_by_id(rate_id)
    
    await callback.message.answer(
        text=f"Вы выбрали тариф {rate.name}. Его цена за месяц = {rate.price}₽\n\nВыберите приобретаемый период",
        reply_markup=await generate_period_keyboard(rate_id)
    )
    
@dp.callback_query(lambda callback: callback.data.startswith("period"))
async def get_period(callback: CallbackQuery):
    await callback.message.delete_reply_markup()
    
    rate_id, period = map(int, callback.data.split(":")[-2:])
    
    rate = await Orm.get_rate_by_id(rate_id)
    
    if period == 1:
        total_amount = rate.price
    else:
        total_amount = eval(f"rate.price_{period}")
    
    await callback.message.answer(
        text=f"Вы выбрали тариф {rate.name} на {period} {await incline_by_period(period)}. Его цена = {total_amount}₽",
    )
    await card_callback(callback.from_user.id, rate, period, total_amount)

async def card_callback(telegram_id: int, rate: Rate, period: int, total_amount: int):
    label = f"Покупка {rate.name} на {period} {await incline_by_period(period)}"
    
    await bot.send_invoice(
        chat_id=telegram_id,
        title=f"Покупка {rate.name}",
        description=label,
        provider_token=PAYMENTS_TOKEN,
        currency="rub",
        prices=[
            LabeledPrice(label=label, amount=total_amount * 100)
        ],
        start_parameter="pay",
        payload=f"{rate.id}:{period}",
    )
    
@dp.pre_checkout_query(lambda query: True)
async def process_pre_checkout_query(pre_checkout_query: PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)
    
@dp.message(F.successful_payment)
async def successful_payment_handler(message: Message):
    payload = message.successful_payment.invoice_payload
    rate_id, period = map(int, payload.split(":"))
    user = await Orm.get_user_by_telegram_id(message.from_user.id)
    await Orm.update_subscription(user, period, rate_id)

    await message.answer("Поздравляю! Вы успешно обновили свой тарифный план")