import uuid
from yookassa import Configuration, Payment
from yookassa.domain.response import PaymentResponse

from bot import bot

from config import YOOKASSA_SHOP_ID, YOOKASSA_SECRET_KEY

from handlers.markups import *

Configuration.configure(YOOKASSA_SHOP_ID, YOOKASSA_SECRET_KEY)

class YooPay:
    shop_id = YOOKASSA_SHOP_ID
    secret_key = YOOKASSA_SECRET_KEY
    
    async def create_payment(self, type_='rate', amount=None , rate_name=None, period=None, telegram_id=None, count_of_generations=None, package_id=None):
        match type_:
            case 'rate': 
                purchase_description = f"Покупка тарифа {rate_name} на {period} {await incline_by_period(period)}"
                metadata = await self.generate_metadata(rate_name=rate_name, period=period, telegram_id=telegram_id)
            case 'midjourney':
                purchase_description = f"Покупка генераций: {count_of_generations} шт."
                metadata = await self.generate_metadata(package_id=package_id, telegram_id=telegram_id)
        response = Payment.create({
            "receipt": {
                "customer": {
                    "email": "tempo@gmail.com",
                },
                "items": [
                    {
                        "description": purchase_description,
                        "amount": {
                            "value": str(amount) + '.00',
                            "currency": "RUB"
                        },
                        "vat_code": 1,
                        "quantity": "1",
                        "measure": "day",
                        "payment_subject": "service",
                        "payment_mode": "full_payment"
                    }
                ],
            },
            "amount": {
                "value": str(amount) + '.00',
                "currency": "RUB"
            },
            "confirmation": {
                "type": "redirect",
                "return_url": f"https://t.me/{(await bot.me()).username}"
            },
            "capture": True,
            "description": purchase_description,
            "metadata": metadata,
            # test
            "test": False}, str(uuid.uuid4())),
            # test
        return response[0]

    async def generate_metadata(self, **kwargs):
        metadata = {
            key: str(value) for key, value in kwargs.items()
        }
        return metadata
    
    async def find_payment(payment_id: str) -> PaymentResponse:
        return Payment.find_one(payment_id)
    
    @staticmethod
    async def payment_success(payment_id: str):
        payment = await YooPay.find_payment(payment_id)
        if payment.status == "succeeded":
            return payment
        else:
            return None