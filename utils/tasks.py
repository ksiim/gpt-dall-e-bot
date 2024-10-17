from models.dbs.orm import Orm


async def clear_free_limits():
    await Orm.clear_free_limits()
    
async def clear_payable_limits():
    await Orm.clear_payable_limits()
    
async def delete_rate():
    await Orm.end_of_subscription()