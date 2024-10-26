import os
from typing import Tuple
from config import ACCOUNT_HASH, USERAPI_UI_API_KEY, USERAPI_UI_URL, OPENAI_API_KEY
from httpx import AsyncClient
import aiofiles


from models.dbs.orm import Orm

# {'account_hash': '0af634d2-7cfc-4201-ae6f-61bd9ee1ea1d',
# 'hash': '3e0ad09e-09ae-46e1-988a-c2a80af7f0a8',
# 'webhook_url': None, 'webhook_type': None,
# 'callback_id': None, 'prompt': 'Синий океан и зеленая трава',
# 'type': 'imagine', 'progress': 100, 'status': 'done',
# 'result': {'url': 'https://cdn.discordapp.com/attachments/1295719054635700308/1299424507055833189/dandangpt______ace5f261-f762-4b0d-9285-25863e674e0c.png?ex=671d26e0&is=671bd560&hm=1d48291c9ac7e4af1e185b82f8f38f95813432f7eb2c1b50b8911d832f406b0a&',
# 'proxy_url': 'https://media.discordapp.net/attachments/1295719054635700308/1299424507055833189/dandangpt______ace5f261-f762-4b0d-9285-25863e674e0c.png?ex=671d26e0&is=671bd560&hm=1d48291c9ac7e4af1e185b82f8f38f95813432f7eb2c1b50b8911d832f406b0a&',
# 'filename': 'dandangpt______ace5f261-f762-4b0d-9285-25863e674e0c.png',
# 'content_type': 'image/png', 'width': 2048, 'height': 2048, 'size': 8655193},
# 'next_actions': [{'type': 'upscale', 'choices': [1, 2, 3, 4]}, {'type': 'reroll'},
# {'type': 'variation', 'choices': [1, 2, 3, 4]}, {'type': 'seed'}],
# 'status_reason': None, 'prefilter_result': [],
# 'created_at': '2024-10-25T17:28:37Z'}

# {'account_hash': '0af634d2-7cfc-4201-ae6f-61bd9ee1ea1d',
# 'hash': '3e0ad09e-09ae-46e1-988a-c2a80af7f0a8',
# 'webhook_url': None, 'webhook_type': None,
# 'callback_id': None, 'prompt': 'Синий океан и зеленая трава',
# 'type': 'imagine', 'progress': 20, 'status': 'progress',
# 'result': None, 'status_reason': None,
# 'prefilter_result': [], 'created_at': '2024-10-25T17:28:37Z'}

class MidJourney:
    API_URL = USERAPI_UI_URL
    ACCOUNT_HASH = ACCOUNT_HASH
    USERAPI_UI_API_KEY = USERAPI_UI_API_KEY
    WEBHOOK_URL = ""
    
    def __init__(self, telegram_id=None):
        self.telegram_id = telegram_id
        
    async def is_limit_reached(self):
        """Проверка на превышение лимита"""
        user = await Orm.get_user_by_telegram_id(self.telegram_id)
        count_of_requests = user.remaining_midjourney_generations
        
        if count_of_requests <= 0:
            return True
        return False

    async def generate_image(self, prompt):
        """Создание изображения по заданному запросу (prompt)"""
        
        if await self.is_limit_reached():
            return None
        
        headers = await self.generate_headers()
        data = await self.generate_data(prompt)
        async with AsyncClient() as client:
            response = await client.post(f"{self.API_URL}imagine", headers=headers, json=data)

        if response.status_code == 200:
            await Orm.decrement_midjourney_generations(self.telegram_id)
            data = response.json()
            hash = data['hash']
            return hash
        return None

    async def generate_headers(self):
        headers = {
            'api-key': self.USERAPI_UI_API_KEY,
            'Content-Type': 'application/json'
        }
        return headers

    async def generate_data(self, prompt):
        data = {
            "prompt": prompt,
            "webhook_url": self.WEBHOOK_URL,
            "webhook_type": "progress",
            "is_disable_prefilter": False
        }
        
        return data


    async def check_image_url(self, task_hash) -> Tuple[str, int, str]:
        """Проверка статуса задачи и получение URL изображения по хэшу задачи"""
        headers = await self.generate_headers()
        
        status_url = f"{self.API_URL}status?hash={task_hash}"
        
        async with AsyncClient() as client:
            response = await client.get(status_url, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            # data = {'account_hash': '0af634d2-7cfc-4201-ae6f-61bd9ee1ea1d', 'hash': '3e0ad09e-09ae-46e1-988a-c2a80af7f0a8', 'webhook_url': None, 'webhook_type': None, 'callback_id': None, 'prompt': 'Синий океан и зеленая трава', 'type': 'imagine', 'progress': 20, 'status': 'progress', 'result': None, 'status_reason': None, 'prefilter_result': [], 'created_at': '2024-10-25T17:28:37Z'}
            # data = {'account_hash': '0af634d2-7cfc-4201-ae6f-61bd9ee1ea1d', 'hash': '3e0ad09e-09ae-46e1-988a-c2a80af7f0a8', 'webhook_url': None, 'webhook_type': None, 'callback_id': None, 'prompt': 'Синий океан и зеленая трава', 'type': 'imagine', 'progress': 100, 'status': 'done', 'result': {'url': 'https://cdn.discordapp.com/attachments/1295719054635700308/1299424507055833189/dandangpt______ace5f261-f762-4b0d-9285-25863e674e0c.png?ex=671d26e0&is=671bd560&hm=1d48291c9ac7e4af1e185b82f8f38f95813432f7eb2c1b50b8911d832f406b0a&', 'proxy_url': 'https://media.discordapp.net/attachments/1295719054635700308/1299424507055833189/dandangpt______ace5f261-f762-4b0d-9285-25863e674e0c.png?ex=671d26e0&is=671bd560&hm=1d48291c9ac7e4af1e185b82f8f38f95813432f7eb2c1b50b8911d832f406b0a&', 'filename': 'dandangpt______ace5f261-f762-4b0d-9285-25863e674e0c.png', 'content_type': 'image/png', 'width': 2048, 'height': 2048, 'size': 8655193}, 'next_actions': [{'type': 'upscale', 'choices': [1, 2, 3, 4]}, {'type': 'reroll'}, {'type': 'variation', 'choices': [1, 2, 3, 4]}, {'type': 'seed'}], 'status_reason': None, 'prefilter_result': [], 'created_at': '2024-10-25T17:28:37Z'}
            status = data.get('status')
            progress = await try_to_int(data.get('progress'))
            image_url = data.get('result').get('url') if data.get('result') else None
            
            return status, progress, image_url
        else:
            return None, None, None
        
    async def variation(self, hash, choice):
        """Генерация изображения, похожего на choice"""
        
        if await self.is_limit_reached():
            return None
        
        headers = await self.generate_headers()
        data = {
            "hash": hash,
            "choice": await try_to_int(choice),
            "webhook_url": self.WEBHOOK_URL,
            "webhook_type": "progress"
        }
        
        async with AsyncClient() as client:
            response = await client.post(f"{self.API_URL}variation", headers=headers, json=data)
        
        if response.status_code == 200:
            await Orm.decrement_midjourney_generations(self.telegram_id)
            data = response.json()
            task_hash = data['hash']
            return task_hash
        
        return None
    
    async def upscale(self, hash, choice):
        """Улучшенное качество изображения choice"""
        headers = await self.generate_headers()
        data = {
            "hash": hash,
            "choice": await try_to_int(choice),
            "webhook_url": self.WEBHOOK_URL,
            "webhook_type": "progress"
        }
        
        async with AsyncClient() as client:
            response = await client.post(f"{self.API_URL}upscale", headers=headers, json=data)
        
        if response.status_code == 200:
            data = response.json()
            task_hash = data['hash']
            return task_hash

        return None
    
    async def reroll(self, hash):
        """Перегенерация изображения"""
        
        if await self.is_limit_reached():
            return None
        
        headers = await self.generate_headers()
        data = {
            "hash": hash
        }
        
        async with AsyncClient() as client:
            response = await client.post(f"{self.API_URL}reroll", headers=headers, json=data)
        
        if response.status_code == 200:
            await Orm.decrement_midjourney_generations(self.telegram_id)
            data = response.json()
            task_hash = data['hash']
            return task_hash
        
        return None
    
    async def save_image(self, image_url):
        """Сохранение изображения по URL"""
        
        max_id = await Orm.get_current_image_id()
        filename = f"images/image{max_id}.png"
        
        async with AsyncClient() as client:
            response = await client.get(image_url)
            async with aiofiles.open(filename, "wb") as file:
                await file.write(response.content)
                return filename
        return None
    
    async def delete_image(self, filename):
        os.remove(filename)
        return True
        
async def try_to_int(value):
    try:
        value = int(value)
    except Exception as e:
        print(e, value)
    return value