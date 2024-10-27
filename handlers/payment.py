from aiogram import F
from aiogram.types import Message, CallbackQuery, PreCheckoutQuery, LabeledPrice

from bot import dp, bot

from config import PAYMENTS_TOKEN
from yookassa import Configuration

from config import YOOKASSA_SHOP_ID, YOOKASSA_SECRET_KEY

from models.dbs.orm import Orm
from models.dbs.models import *

from .callbacks import *
from .markups import *
from .states import *

from utils.payments import YooPay

    
@dp.callback_query(F.data == "get_midjourney_package")
async def get_midjourney_package(callback: CallbackQuery):
    await callback.message.delete_reply_markup()
    
    await callback.message.answer(
        text="Выберите пакет",
        reply_markup=await generate_midjourney_packages_keyboard(),
    )
    
@dp.callback_query(lambda callback: callback.data.startswith("buy_midjourney"))
async def buy_midjourney_package(callback: CallbackQuery):
    await callback.message.delete()
    
    package_id = int(callback.data.split(":")[-1])
    
    package = await Orm.get_midjourney_package_by_id(package_id)
    
    answer = await callback.message.answer(
        text=f"Вы выбрали пакет генераций {package.count_of_generations}шт. Его цена = {package.price}₽",
    )
    await card_callback(
        type_='midjourney',
        telegram_id=callback.from_user.id,
        count_of_generations=package.count_of_generations,
        total_amount=package.price,
        package_id=package_id
    )
    await asyncio.sleep(10)
    await answer.delete()

@dp.callback_query(lambda callback: callback.data.startswith("buy_rate"))
async def choose_period(callback: CallbackQuery):
    await callback.message.delete()
    
    rate_id = int(callback.data.split(":")[-1])
    
    rate = await Orm.get_rate_by_id(rate_id)
    
    await callback.message.answer(
        text=f"Вы выбрали тариф {rate.name}. Его цена за месяц = {rate.price}₽\n\nВыберите приобретаемый период",
        reply_markup=await generate_period_keyboard(rate_id)
    )
    
@dp.callback_query(lambda callback: callback.data.startswith("period"))
async def get_period(callback: CallbackQuery):
    await callback.message.delete()
    
    rate_id, period = map(int, callback.data.split(":")[-2:])
    
    rate = await Orm.get_rate_by_id(rate_id)
    
    if period == 1:
        total_amount = rate.price
    else:
        total_amount = eval(f"rate.price_{period}")
    
    answer = await callback.message.answer(
        text=f"Вы выбрали тариф {rate.name} на {period} {await incline_by_period(period)}. Его цена {total_amount}₽",
    )
    await card_callback(
        type_='rate',
        telegram_id=callback.from_user.id,
        rate=rate,
        period=period,
        total_amount=total_amount
    )
    await asyncio.sleep(10)
    await answer.delete()

async def card_callback(type_='rate', telegram_id=None, rate=None, period=None, total_amount=None, count_of_generations=None, package_id=None):
    yoopay = YooPay()
    match type_:
        case 'rate':
            response = await yoopay.create_payment(
                amount=total_amount,
                rate_name=rate.name,
                period=period,
                telegram_id=telegram_id
            )
        case 'midjourney':
            response = await yoopay.create_payment(
                type_=type_,
                amount=total_amount,
                count_of_generations=count_of_generations,
                package_id=package_id,
                telegram_id=telegram_id,
            )
    payment_id = response.id
    payment_link = response.confirmation.confirmation_url
    
    await bot.send_message(
        chat_id=telegram_id,
        text="Совершите оплату по ссылке ниже",
        reply_markup=await generate_payment_keyboard(payment_link=payment_link, payment_id=payment_id, type_=type_)
    )
    
@dp.callback_query(lambda callback: callback.data.startswith("check_payment"))
async def check_payment_callback(callback: CallbackQuery):
    _, type_, payment_id = callback.data.split(":")
    payment = await YooPay.payment_success(payment_id)
    if payment:
        match type_:
            case 'rate':
                answer = await process_successful_rate_payment(callback, payment)
            case 'midjourney':
                answer = await process_successful_midjourney_payment(callback, payment)
    else:
        answer = await callback.message.answer("Оплата не прошла")
        
    await asyncio.sleep(3)
    await answer.delete()
    
async def process_successful_midjourney_payment(callback: CallbackQuery, payment):
    await callback.message.delete()
    answer = await callback.message.answer("✅Оплата прошла успешно!")
    user = await Orm.get_user_by_telegram_id(callback.from_user.id)
    package_id = int(payment.metadata["package_id"])
    package = await Orm.get_midjourney_package_by_id(package_id)
    await Orm.add_midjourney_generations(user.telegram_id, package.count_of_generations)
    
    await callback.message.answer("Поздравляю! Пакет успешно активирован, проверьте в разделе /profile")

    return answer

async def process_successful_rate_payment(callback, payment):
    await callback.message.delete()
    answer = await callback.message.answer("✅Оплата прошла успешно!")
    user = await Orm.get_user_by_telegram_id(callback.from_user.id)
    period = int(payment.metadata["period"])
    rate_name = payment.metadata["rate_name"]
    rate = await Orm.get_rate_by_name(rate_name)
    rate_id = rate.id
    await Orm.update_subscription(user, period, rate_id)
    await Orm.add_midjourney_generations(callback.from_user.id, rate.midjourney_generations * period)

    await callback.message.answer("Поздравляю! Подписка успешно активирована, проверьте в разделе /profile")
    return answer

# async def card_callback(telegram_id: int, rate: Rate, period: int, total_amount: int):
#     label = f"Покупка {rate.name} на {period} {await incline_by_period(period)}"
    
#     await bot.send_invoice(
#         chat_id=telegram_id,
#         title=f"Покупка {rate.name}",
#         description=label,
#         provider_token=PAYMENTS_TOKEN,
#         currency="rub",
#         prices=[
#             LabeledPrice(label=label, amount=total_amount * 100)
#         ],
#         start_parameter="pay",
#         payload=f"{rate.id}:{period}",
#     )
    
# @dp.pre_checkout_query(lambda query: True)
# async def process_pre_checkout_query(pre_checkout_query: PreCheckoutQuery):
#     await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)
    
# @dp.message(F.successful_payment)
# async def successful_payment_handler(message: Message):
#     payload = message.successful_payment.invoice_payload
#     rate_id, period = map(int, payload.split(":"))
#     user = await Orm.get_user_by_telegram_id(message.from_user.id)
#     await Orm.update_subscription(user, period, rate_id)

#     await message.answer("Поздравляю! Вы успешно обновили свой тарифный план")