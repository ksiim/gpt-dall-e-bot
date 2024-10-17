import asyncio

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton, WebAppInfo

from bot import bot

from models.dbs.orm import Orm
from models.dbs.models import *

from .callbacks import *


waiting_text = "Ваш запрос принят, ожидайте ответа..."

async def generate_rates_info_text():
    return f"""
Доступ к лучшим AI-сервисам прямо в Telegram:

Бесплатно | ЕЖЕНЕДЕЛЬНО
✔️ 50 текстовых запросов
✔️ GPT-4o mini
(Изменить модель в /model)

✅ PLUS | МЕСЯЦ
✔️ 100 запросов GPT-4o mini ежедневно
✔️ 50 запросов GPT-4o
🌅 10 картинок Dall-E

Стоимость: 299 р.

🔥Pro X2 | МЕСЯЦ
✌️ Увеличивает лимит в 2 раза:
✔️ 200 запросов GPT-4o mini ежедневно
✔️ 100 запроосв GPT-4o
🌅 20 картинок Dall-E
Стоимость: 499 р.

💬 По вопросам оплаты: @GPT_helpAi
"""

discount = {
    1: 1,
    3: 0.95,
    6: 0.9,
    12: 0.8
}

async def generate_profile_text(user: User):
    return f"""Это ваш профиль
ID: {user.telegram_id}
Подписка: {await rate_name(user.rate.id)}
{"\n" if user.rate_id > 1 else "Чтобы добавить подписку, нажмите /premium\n"}
**Лимиты**
{await generate_limits_text(user)}
Обновление лимитов {'каждую неделю в понедельник' if user.rate.name == 'free' else 'каждый день'} в 00:00"""

async def generate_payment_keyboard(payment_link: str, payment_id: str):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Оплатить",
                    web_app=WebAppInfo(
                        url=payment_link,
                    )
                ),
                InlineKeyboardButton(
                    text="Проверить оплату",
                    callback_data=f"check_payment:{payment_id}"
                )
            ]
        ]
    )

async def rate_name(rate_id):
    match rate_id:
        case 1:
            return 'Стандартная ☑️'
        case 2:
            return 'Plus ✅'
        case 3:
            return 'Pro 🔥'
            

async def generate_change_rate_text():
    rates = await Orm.get_rates_for_sell()
    result = ""
    for rate in rates:
        result += f"Тариф **{rate.name.capitalize()}** - {rate.price}₽/месяц\n"
        for model in rate.models_limits:
            result += f"    Модель: {model.model.replace('_', '-')} - {model.daily_limit} {await incline_by_limit(model.daily_limit)}\n"
        result += "\n"
    return result
    
async def incline_by_limit(limit):
    if limit > 20:
        limit = limit % 10
        
    if limit == 1:
        return "запрос"
    elif limit in (2, 3, 4):
        return "запроса"
    else:
        return "запросов"
    
async def generate_limits_text(user: User):
    chat_model_enum_value = user.chat_model.value
    chat_model_enum_name = ChatModelEnum(chat_model_enum_value).name
    limit_chat = user.rate.daily_limit_dict[chat_model_enum_name]
    image_model_enum_value = user.image_model.value
    image_model_enum_name = ImageModelEnum(image_model_enum_value).name
    limit_image = user.rate.daily_limit_dict[image_model_enum_name]
    return f"""✍️{chat_model_enum_value} - {limit_chat - await get_count_of_requests(chat_model_enum_name, user)}/{limit_chat}
🖼{image_model_enum_value} - {limit_image - await get_count_of_requests(image_model_enum_name, user)}/{limit_image}
"""

async def get_count_of_requests(model: str, user):
    count_of_requests = await Orm.get_count_of_requests(model, telegram_id=user.telegram_id)
    return count_of_requests

async def generate_current_models_text(user: User):
    return f"""
ChatGPT-4o:

🌟 Полноценная версия GPT-4, предоставляющая высокую точность в генерации ответов
🧠 Идеальна для сложных текстовых задач

ChatGPT-4o mini:

🎯 Подходит для простых задач, где не требуется высокая вычислительная мощность или сложная аналитика
    """

async def generate_statistic_text():
    yesterday, today, all_users_count, online_count = await asyncio.gather(
        Orm.get_yesterday_count(),
        Orm.get_today_count(),
        Orm.get_all_users_count(),
        Orm.get_online_count(),
    )

    try:
        diff = int((today / yesterday - 1) * 100)
    except ZeroDivisionError:
        diff = 0

    arrow_text = f"↑{diff}%" if diff >= 0 else f"↓{diff}%"
    return f"""📈 Статистика

✅ Сегодня в бота пришло {today} чел. ({arrow_text})
✅ Вчера в бота пришло {yesterday} чел.

🔥 Всего пользователей: {all_users_count}

👉 онлайн {online_count}
"""

async def generate_rates_keyboard():
    rates = await Orm.get_rates_for_sell()
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=" ".join([r.upper() for r in rate.name.split()]),
                    callback_data=f"buy_rate:{rate.id}"
                ) for rate in rates
            ]
        ]
    )
    
async def incline_by_period(period):
    if period == 1:
        return "месяц"
    elif period in (2, 3, 4):
        return "месяца"
    else:
        return "месяцев"
    
async def generate_period_keyboard(rate_id: int):
    rate = await Orm.get_rate_by_id(rate_id)
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"1 Месяц {rate.price}₽",
                    callback_data=f"period:{rate_id}:1"
                ),
                InlineKeyboardButton(
                    text=f"3 Месяца {rate.price_3}₽",
                    callback_data=f"period:{rate_id}:3"
                ),
            ],
            [
                InlineKeyboardButton(
                    text=f"6 Месяцев {rate.price_6}₽",
                    callback_data=f"period:{rate_id}:6"
                ),
                InlineKeyboardButton(
                    text=f"12 Месяцев {rate.price_12}₽",
                    callback_data=f"period:{rate_id}:12"
                ),
            ]
        ]
    )

async def generate_start_text(message):
    return f"""Рад тебя приветствовать, {message.from_user.full_name}! Я Telegram бот ChatGPT + Dall-E

Можешь задавать мне любые вопросы, просто напиши 😉

Узнать все команды /help"""

help_text = """
Этот бот открывает вам доступ к продуктам OpenAI, таким как ChatGPT, Midjourney и Dall-E, для создания текста и изображений.

Чатбот умеет:
1. Писать и редактировать тексты
2. Переводить с любого языка на любой
3. Писать и редактировать код
4. Отвечать на вопросы

🤖 Бот использует ту же модель, что и сайт ChatGPT

✍️ Для получения текстового ответа просто напишите Ваш вопрос в чат

🌅 Для создания изображения начните сообщение с /img и добавьте описание

🔄 Чтобы очистить контекст диалога, воспользуйтесь командой /reset 

Команды
/start - Что умеет чат-бот
/profile - профиль пользователя
/premium- купить подписку
/reset - сброс контекста
/mode - выбрать нейросеть
/img - генерация изображений
/help - помощь
"""

close_markup = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="Закрыть", callback_data="close")
        ]
    ]
)

async def generate_model_markup(user: User):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅" + e.value if user.chat_model.value == e.value else "" + e.value,
                    callback_data=f"change_to:{e.name}"
                )
                ] for e in ChatModelEnum
        ]
    )

buy_premium_markup = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="Обновить тарифный план",
                callback_data="change_rate"
            )
        ]
    ]
)