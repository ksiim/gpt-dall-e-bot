import asyncio

from models.databases import Session, AsyncSession
from models.dbs.models import *

from sqlalchemy.orm import joinedload
from sqlalchemy import and_, func, insert, inspect, or_, select, text, delete, update, event
import datetime

def before_insert_listener(mapper, connection, target):
    loop = asyncio.get_event_loop()
    loop.create_task(run_async_before_insert_listener(target))

async def run_async_before_insert_listener(target):
    async with Session() as session:
        await Orm.set_default_rate(session, target)

class Orm:
    
    @staticmethod
    async def create_payable_rates():
        async with Session() as session:
            rate_1 = Rate(
                name='plus',
                price=299,
                price_3=799,
                price_6=1399,
                price_12=2490,
                models_limits=[
                    ModelLimit(model=ChatModelEnum.GPT_4O_MINI.name, daily_limit=100),
                    ModelLimit(model=ChatModelEnum.GPT_4O.name, daily_limit=50),
                    ModelLimit(model=ImageModelEnum.DALL_E_3.name, daily_limit=10),
                ]
            )
            rate_2 = Rate(
                name='pro',
                price=499,
                price_3=1299,
                price_6=2399,
                price_12=3899,
                models_limits=[
                    ModelLimit(model=ChatModelEnum.GPT_4O_MINI.name, daily_limit=200),
                    ModelLimit(model=ChatModelEnum.GPT_4O.name, daily_limit=100),
                    ModelLimit(model=ImageModelEnum.DALL_E_3.name, daily_limit=20),
                ]
            )
            session.add(rate_1)
            session.add(rate_2)
            await session.commit()
    
    @staticmethod
    async def fill_rates():
        async with Session() as session:
            query = select(Rate).join(ModelLimit)
            rates = (await session.execute(query)).unique().scalars().all()
            if not rates:
                await Orm.create_free_rate()
                await Orm.create_payable_rates()
            elif len(rates) == 1:
                await Orm.create_payable_rates()
    
    @staticmethod
    async def end_of_subscription():
        async with Session() as session:
            query = (
                select(User)
                .where(User.subscription_end_time != None)
                .where(User.subscription_end_time < datetime.datetime.now())
            )
            users_to_delete = (await session.execute(query)).unique().scalars().all()
            for user in users_to_delete:
                query = update(User).where(User.id == user.id).values(rate_id=1, subscription_end_time=None)
                await session.execute(query)
            await session.commit()
    
    @staticmethod
    async def update_subscription(user: User, month_period: int, rate_id: int):
        async with Session() as session:
            user.subscription_end_time = datetime.datetime.now() + datetime.timedelta(days=30 * month_period)
            user.rate_id = rate_id
            session.add(user)
            await session.commit()
    
    @staticmethod
    async def get_rate_by_id(rate_id):
        async with Session() as session:
            query = select(Rate).where(Rate.id == rate_id)
            rate = (await session.execute(query)).unique().scalar_one_or_none()
            return rate
        
    @staticmethod
    async def get_rate_by_name(rate_name):
        async with Session() as session:
            query = select(Rate).where(Rate.name == rate_name)
            rate = (await session.execute(query)).unique().scalar_one_or_none()
            return rate
    
    @staticmethod
    async def get_rates_for_sell():
        async with Session() as session:
            query = (
                select(Rate)
                .where(Rate.price > 0)
                .options(joinedload(Rate.models_limits))
            )
            rates = (await session.execute(query)).unique().scalars().all()
            return rates
    
    @staticmethod
    async def clear_context_messages(user_id: int):
        async with Session() as session:
            query = delete(AIMessage).where(AIMessage.user_id == user_id)
            await session.execute(query)
            await session.commit()
    
    @staticmethod
    async def update_chat_model(user: User, model: str) -> None:
        async with Session() as session:
            user.chat_model = model
            session.add(user)
            await session.commit()
            await session.refresh(user)
            return user
    
    @staticmethod
    async def add_context_message(user: User, content: str, role: str):
        async with Session() as session:
            await Orm.remove_oldest_message(user.id)
            ai_message = AIMessage(user_id=user.id, content=content, role=role)
            session.add(ai_message)
            await session.commit()
            await session.refresh(ai_message)
            return ai_message
        
    @staticmethod
    async def remove_oldest_message(user_id):
        async with Session() as session:
            query = (
                select(AIMessage)
                .where(AIMessage.user_id == user_id)
                .order_by(AIMessage.id)
            )
            results = (await session.execute(query)).scalars().all()
            if len(results) > 9:
                await session.delete(results[0])
                await session.commit()
    
    @staticmethod
    async def get_context_messages(user: User):
        async with Session() as session:
            query = select(AIMessage).where(User.telegram_id == user.telegram_id).join(User)
            context_messages = (await session.execute(query)).scalars().all()
            result = list()
            for context_message in context_messages:
                dictionary = {"role": str(context_message.role), "content": str(context_message.content)}
                result.append(dictionary)
            return result
    
    @staticmethod
    async def get_admins_ids():
        async with Session() as session:
            query = select(User.telegram_id).where(User.admin == True)
            admins_ids = (await session.execute(query)).scalars().all()
            return admins_ids
    
    @staticmethod
    async def get_all_users_count():
        async with Session() as session:
            query = select(func.count(User.id))
            return (await session.execute(query)).scalar()
    
    @staticmethod
    async def get_online_count():
        async with Session() as session:
            query = select(func.count(User.id)).where(User.last_activity_time > datetime.datetime.now() - datetime.timedelta(minutes=3))
            return (await session.execute(query)).scalar()
    
    @staticmethod
    async def get_today_count():
        async with Session() as session:
            today = datetime.datetime.now().replace(hour=0, minute=0, second=0)
            query = select(func.count(User.id)).where(User.registration_time >= today)
            return (await session.execute(query)).scalar()
    
    @staticmethod
    async def get_yesterday_count():
        async with Session() as session:
            one_day_ago = datetime.datetime.now().replace(hour=0, minute=0, second=0) - datetime.timedelta(days=1)
            today = datetime.datetime.now().replace(hour=0, minute=0, second=0)
            query = select(func.count(User.id)).where(User.registration_time.between(one_day_ago, today))
            return (await session.execute(query)).scalar()
    
    @staticmethod
    async def create_empty_count_of_requests(model, telegram_id):
        async with Session() as session:
            user = await Orm.get_user_by_telegram_id(telegram_id)
            count_of_requests = CountOfRequests(user_id=user.id, model=model, count=0)
            session.add(count_of_requests)
            await session.commit()
            await session.refresh(count_of_requests)
            return count_of_requests
    
    @staticmethod
    async def create_free_rate():
        async with Session() as session:
            rate = Rate(
                name='free',
                price=0,
                price_3=0,
                price_6=0,
                price_12=0,
                models_limits=[
                    ModelLimit(model=ChatModelEnum.GPT_4O_MINI.name, daily_limit=50),
                    ModelLimit(model=ChatModelEnum.GPT_4O.name, daily_limit=0),
                    ModelLimit(model=ImageModelEnum.DALL_E_3.name, daily_limit=2),
                ]
            )
            session.add(rate)
            await session.commit()
            await session.refresh(rate)
            return rate.id
    
    @staticmethod
    async def set_default_rate(session: AsyncSession, user: User):
        async with Session() as session:
            query = select(Rate).where(Rate.name == 'free')
            default_rate = await session.execute(query)
            default_rate = default_rate.scalars().first()
            if default_rate:
                user.rate_id = default_rate.id
            else:
                default_rate_id = await Orm.create_free_rate()
                user.rate_id = default_rate_id
    
    @staticmethod
    async def update_count_of_requests(model, user: User):
        async with Session() as session:
            count_of_requests = user.count_of_requests_dict.get(model)
            if count_of_requests is None:
                count_of_requests = (await Orm.create_empty_count_of_requests(model, user.telegram_id)).count
            query = update(CountOfRequests).where(and_(CountOfRequests.user_id == user.id, CountOfRequests.model == model)).values(count=count_of_requests + 1)
            await session.execute(query)
            await session.commit()
    
    @staticmethod
    async def get_count_of_requests(model, telegram_id) -> int:
        async with Session() as session:
            user = await Orm.get_user_by_telegram_id(telegram_id)
            query = select(CountOfRequests).where(and_(CountOfRequests.user_id == user.id, CountOfRequests.model == model))
            count_of_requests = (await session.execute(query)).scalar_one_or_none()
            return count_of_requests.count if count_of_requests \
                else (await Orm.create_empty_count_of_requests(model, telegram_id)).count

    @staticmethod
    async def get_request_type(model):
        return TypeOfRequestEnum.CHAT if model in await get_all_enum_values(ChatModelEnum) else TypeOfRequestEnum.IMAGE
    
    @staticmethod
    async def update_online(telegram_id):
        async with Session() as session:
            query = (
                update(User)
                .where(User.telegram_id == telegram_id)
                .values(last_activity_time=datetime.datetime.now())
                .options(joinedload(User.rate))
            )
            await session.execute(query)
            await session.commit()
    
    @staticmethod
    async def clear_free_limits():
        async with Session() as session:
            query = select(CountOfRequests).where(Rate.price == 0).join(User).join(Rate)
            results = await session.execute(query)
            for result in results.scalars().all():
                await session.delete(result)
            await session.commit()
            
    @staticmethod
    async def clear_payable_limits():
        async with Session() as session:
            query = select(CountOfRequests).where(Rate.price > 0).join(User).join(Rate)
            results = await session.execute(query)
            for result in results.scalars().all():
                await session.delete(result)
            await session.commit()
    
    @classmethod
    async def create_user(cls, message):
        if await cls.get_user_by_telegram_id(message.from_user.id) is None:
            user = User(
                full_name=message.from_user.full_name,
                telegram_id=int(message.from_user.id),
                username=message.from_user.username
            )
            await cls.save_user(user)
    
    @staticmethod
    async def save_user(user):
        async with Session() as session:
            await Orm.set_default_rate(session, user)
            await session.merge(user)
            await session.commit()
    
    @staticmethod
    async def get_user_by_telegram_id(telegram_id):
        async with Session() as session:
            query = (
                select(User)
                .where(User.telegram_id == telegram_id)
                .options(
                    joinedload(User.rate).joinedload(Rate.models_limits),
                    joinedload(User.count_of_requests),
                )
            )
            user = (await session.execute(query)).unique().scalar_one_or_none()
            return user
    
    @staticmethod
    async def get_all_users():
        async with Session() as session:
            query = select(User)
            users = (await session.execute(query)).scalars().all()
            return users
        