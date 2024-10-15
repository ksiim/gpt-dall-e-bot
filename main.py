import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from bot import dp, bot

import logging

import handlers

import handlers.middlewares
import handlers.openai_api
import handlers.tasks
from models.databases import create_database


logging.basicConfig(level=logging.INFO)

async def main():
    dp.message.middleware(handlers.middlewares.OnlineMiddleware())
    
    scheduler = AsyncIOScheduler()
    scheduler.add_job(handlers.tasks.clear_free_limits, 'cron', day_of_week="mon", hour=0)
    scheduler.add_job(handlers.tasks.clear_payable_limits, 'cron', hour=0)
    scheduler.add_job(handlers.tasks.delete_rate, 'cron', hour=0)
    # scheduler.add_job(handlers.tasks.delete_rate, 'interval', seconds=5)
    # scheduler.add_job(handlers.tasks.clear_free_limits, 'interval', seconds=35)
    # scheduler.add_job(handlers.tasks.clear_payable_limits, 'interval', seconds=35)
    scheduler.start()
    
    await create_database()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())