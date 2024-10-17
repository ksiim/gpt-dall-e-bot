from yookassa import Configuration, Payment
from yookassa.domain.response import PaymentResponse

from bot import bot

from config import YOOKASSA_SHOP_ID, YOOKASSA_SECRET_KEY

from handlers.markups import *


Configuration.account_id = YOOKASSA_SHOP_ID
Configuration.secret_key = YOOKASSA_SECRET_KEY

class YooPay:
    shop_id = YOOKASSA_SHOP_ID
    secret_key = YOOKASSA_SECRET_KEY
    
    def __init__(self, amount: int, rate_name: str, period: int, telegram_id: int):
        self.amount = amount
        self.rate_name = rate_name
        self.period = period
        self.telegram_id = telegram_id
    
    async def create_payment(self):
        response = Payment.create({
            "receipt": {
                "customer": {
                    "email": "tempo@gmail.com",
                },
                "items": [
                    {
                        "description": f"Покупка тарифа {self.rate_name} на {self.period} {await incline_by_period(self.period)}",
                        "amount": {
                            "value": str(self.amount) + '.00',
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
                "value": str(self.amount) + '.00',
                "currency": "RUB"
            },
            "confirmation": {
                "type": "redirect",
                "return_url": f"https://t.me/{(await bot.me()).username}"
            },
            "capture": True,
            "description": f"Покупка тарифа {self.rate_name} на {self.period} {await incline_by_period(self.period)}",
            "metadata": {
                "telegram_id": self.telegram_id,
                "rate_name": self.rate_name,
                "period": self.period
            },
            # test
            "test": False}),
            # test
        return response[0]
    
    async def find_payment(payment_id: str) -> PaymentResponse:
        return Payment.find_one(payment_id)
    
    @staticmethod
    async def payment_success(payment_id: str):
        payment = await YooPay.find_payment(payment_id)
        if payment.status == "succeeded":
            return payment
        else:
            return None