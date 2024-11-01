import asyncio
from sys import exception

from aiogram.types import (
    InlineKeyboardButton, InlineKeyboardMarkup,
    ReplyKeyboardMarkup, KeyboardButton, WebAppInfo,
    Message
)

from bot import bot

from models.dbs.orm import Orm
from models.dbs.models import *
from utils import midjourney

from .callbacks import *


waiting_text = "Ваш запрос принят, ожидайте ответа..."

exception_on_midjourney_text = "Чтобы отправлять запросы к Midjorney нужно приобрести пакет или подписку по команде /premium"

async def generate_rates_info_text():
    free_rate = await Orm.get_rate_by_name("free")
    plus_rate = await Orm.get_rate_by_name("plus")
    pro_rate = await Orm.get_rate_by_name("pro")
    free_rate_gpt_4o_mini = str(free_rate.daily_limit_dict[ChatModelEnum.GPT_4O_MINI.name])
    plus_rate_gpt_4o_mini = str(plus_rate.daily_limit_dict[ChatModelEnum.GPT_4O_MINI.name])
    plus_rate_dall_e = str(plus_rate.daily_limit_dict[ImageModelEnum.DALL_E_3.name])
    plus_rate_price = str(plus_rate.price)
    pro_rate_gpt_4o = str(pro_rate.daily_limit_dict[ChatModelEnum.GPT_4O.name])
    pro_rate_gpt_4o_mini = str(pro_rate.daily_limit_dict[ChatModelEnum.GPT_4O_MINI.name])
    pro_rate_dall_e = str(pro_rate.daily_limit_dict[ImageModelEnum.DALL_E_3.name])
    pro_rate_price = str(pro_rate.price)
    return f"""
Доступ к лучшим нейросетям прямо в Telegram:

Бесплатно | ЕЖЕНЕДЕЛЬНО
✔️ {free_rate_gpt_4o_mini} текстовых запросов
✔️ GPT-4o mini
(Изменить модель в /model)

✅ PLUS | МЕСЯЦ
✅ {plus_rate_gpt_4o_mini} запросов GPT-4o mini ежедневно
🌅 {plus_rate_dall_e} картинок Dall-E
✨ Распознавание голосовых сообщений и изображений
🌄 10 изображений Midjorney 6.1 /mj

Стоимость: {plus_rate_price} р.

🔥Pro | МЕСЯЦ
✨Больше лимитов:
✅ {pro_rate_gpt_4o_mini} запросов GPT-4o mini ежедневно
✅ {pro_rate_gpt_4o} запросов GPT-4o
🌅 {pro_rate_dall_e} картинок Dall-E
✨ Распознавание голосовых сообщений и изображений
🌄 20 изображений Midjorney 6.1 /mj

Стоимость: {pro_rate_price} р.

MIDJORNEY - ПАКЕТ
🌄 от 50 до 500 генераций
🌄 Midjorney 6.1 /mj
✅ промпты на русском языке

Стоимость: от 299 р.

💬 По вопросам оплаты: @GPT_helpAi
"""

prompt_taken_message_text = "✅ Запрос принят. Генерирую изображение, это может занять 1-2 минуты..."

discount = {
    1: 1,
    3: 0.95,
    6: 0.9,
    12: 0.8
}

async def generate_midjourney_markup(hash):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text='U1',
                    callback_data=f"upscale:{hash}:1"
                ),
                InlineKeyboardButton(
                    text='U2',
                    callback_data=f"upscale:{hash}:2"
                ),
                InlineKeyboardButton(
                    text='U3',
                    callback_data=f"upscale:{hash}:3"
                ),
                InlineKeyboardButton(
                    text='U4',
                    callback_data=f"upscale:{hash}:4"
                ),
            ],
            [
                InlineKeyboardButton(
                    text='V1',
                    callback_data=f"variation:{hash}:1"
                ),
                InlineKeyboardButton(
                    text='V2',
                    callback_data=f"variation:{hash}:2"
                ),
                InlineKeyboardButton(
                    text='V3',
                    callback_data=f"variation:{hash}:3"
                ),
                InlineKeyboardButton(
                    text='V4',
                    callback_data=f"variation:{hash}:4"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🔄",
                    callback_data=f"reroll:{hash}"
                )
            ]
        ]
    )

async def generate_profile_text(user: User):
    return f"""Это ваш профиль
ID: {user.telegram_id}
Подписка: {await rate_name(user.rate.id)}
{"\n" if user.rate_id > 1 else "Чтобы добавить подписку, нажмите /premium\n"}
**Лимиты**
{await generate_limits_text(user)}
Обновление лимитов {'каждую неделю в понедельник' if user.rate.name == 'free' else 'каждый день'} в 00:00"""

async def generate_payment_keyboard(payment_link: str, payment_id: str, type_='rate'):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Оплатить",
                    url=payment_link,
                ),
                InlineKeyboardButton(
                    text="Проверить оплату",
                    callback_data=f"check_payment:{type_}:{payment_id}"
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
    rate = user.rate
    limit_gpt_4o = rate.daily_limit_dict[ChatModelEnum.GPT_4O.name]
    limit_gpt_4o_mini = rate.daily_limit_dict[ChatModelEnum.GPT_4O_MINI.name]
    image_model_enum_value = user.image_model.value
    image_model_enum_name = ImageModelEnum(image_model_enum_value).name
    limit_image = rate.daily_limit_dict[image_model_enum_name]
    remaining_midjourney_generations = user.remaining_midjourney_generations
    return f"""✍️{ChatModelEnum.GPT_4O.value} - {limit_gpt_4o - await get_count_of_requests(ChatModelEnum.GPT_4O.name, user)}/{limit_gpt_4o}
✍️{ChatModelEnum.GPT_4O_MINI.value} - {limit_gpt_4o_mini - await get_count_of_requests(ChatModelEnum.GPT_4O_MINI.name, user)}/{limit_gpt_4o_mini}
🖼{image_model_enum_value} - {limit_image - await get_count_of_requests(image_model_enum_name, user)}/{limit_image}
🖼Midjourney - {remaining_midjourney_generations} шт.
"""

async def get_count_of_requests(model: str, user: User):
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
    (yesterday, today, all_users_count,
    online_count, last_week_count,
    last_month_count) = await asyncio.gather(
        Orm.get_yesterday_count(),
        Orm.get_today_count(),
        Orm.get_all_users_count(),
        Orm.get_online_count(),
        Orm.get_last_week_count(),
        Orm.get_last_month_count()
    )

    try:
        diff = int((today / yesterday - 1) * 100)
    except ZeroDivisionError:
        diff = 0

    arrow_text = f"↑{diff}%" if diff >= 0 else f"↓{diff}%"
    return f"""📈 Статистика

✅ Сегодня в бота пришло {today} чел. ({arrow_text})
✅ Вчера в бота пришло {yesterday} чел.
✅ За последнюю неделю в бота пришло {last_week_count} чел.
✅ За последний месяц в бота пришло {last_month_count} чел.

🔥 Всего пользователей: {all_users_count}

👉 онлайн {online_count}
"""

async def generate_rates_keyboard():
    rates = await Orm.get_rates_for_sell()
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Получить " + " ".join([r.upper() for r in rate.name.split()]),
                    callback_data=f"buy_rate:{rate.id}"
                ) for rate in rates
            ]
        ] + [
            [
                InlineKeyboardButton(
                    text="Получить пакет Midjourney",
                    callback_data="get_midjourney_package"
                )
            ]
        ]
    )
    
async def generate_midjourney_packages_keyboard():
    mj_prices = await Orm.get_midjourney_counts_and_prices()
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"{mj_price.count_of_generations} генераций - {mj_price.price}₽",
                    callback_data=f"buy_midjourney:{mj_price.id}"
                )
            ] for mj_price in mj_prices
        ]
    )
    return keyboard
    
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

async def generate_start_text(message: Message):
    return f"""Рад тебя приветствовать, {message.from_user.full_name}! Я Telegram бот ChatGPT + MidJourney

Можешь задавать мне любые вопросы, просто напиши 😉

Узнать все команды /help"""

help_text = """
Этот бот открывает вам доступ к продуктам OpenAI и другим нейросетям, таким как ChatGPT и Dall-E 3, для создания текста и изображений.

Чатбот умеет:
1. Писать и редактировать тексты
2. Переводить с любого языка на любой
3. Писать и редактировать код
4. Отвечать на вопросы

🤖 Бот использует ту же модель, что и сайт ChatGPT

✍️ Для получения текстового ответа просто напишите Ваш вопрос в чат

Для создания изображения DALL-E 3 начните сообщение с /dalle

🔄 Чтобы очистить контекст диалога, воспользуйтесь командой /reset

Команды
/start - Что умеет чат-бот
/profile - профиль пользователя
/reset - сброс контекста
/model - выбрать нейросеть
/dalle - изображение Dall-e
/help - помощь
"""

close_markup = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="Закрыть", callback_data="close")
        ]
    ]
)

describe_image_rate_text = 'Чтобы получить описание изображения, нужно оформить подписку Plus или PRO по команде /premium'
voice_rate_text = 'Чтобы нейросеть распознавала голосовые сообщения, нужно оформить подписку Plus или PRO по команде /premium'
buy_premium_text = "Чтобы отправлять запросы к ChatGPT-4o нужно оформить подписку Plus или PRO по команде /premium"

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
                text="🔥Получить премиум",
                callback_data="change_rate"
            )
        ]
    ]
)