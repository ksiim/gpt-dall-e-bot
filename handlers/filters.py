from aiogram.filters import Filter
from aiogram.types import Message
from models.dbs.orm import Orm

class IsAdmin(Filter):
    
    async def __call__(self, message: Message):
        return message.from_user.id in await Orm.get_admins_ids()