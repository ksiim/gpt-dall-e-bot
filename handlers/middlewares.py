import datetime
from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import Message

from models.dbs.orm import Orm

class OnlineMiddleware(BaseMiddleware):
    def __init__(self) -> None:
        return
    
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        
        try:
            await Orm.update_online(event.from_user.id)
        finally:
            return await handler(event, data)