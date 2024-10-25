from typing import Tuple
from config import ACCOUNT_HASH, USERAPI_UI_API_KEY, USERAPI_UI_URL, OPENAI_API_KEY
from httpx import AsyncClient

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
    
    def __init__(self):
        pass

    async def generate_image(self, prompt):
        """Создание изображения по заданному запросу (prompt)"""
        
        headers = await self.generate_headers()
        data = await self.generate_data(prompt)
        async with AsyncClient() as client:
            response = await client.post(f"{self.API_URL}imagine", headers=headers, json=data)

        if response.status_code == 200:
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
            # data = response.json()
            data = {'account_hash': '0af634d2-7cfc-4201-ae6f-61bd9ee1ea1d', 'hash': '3e0ad09e-09ae-46e1-988a-c2a80af7f0a8', 'webhook_url': None, 'webhook_type': None, 'callback_id': None, 'prompt': 'Синий океан и зеленая трава', 'type': 'imagine', 'progress': 20, 'status': 'progress', 'result': None, 'status_reason': None, 'prefilter_result': [], 'created_at': '2024-10-25T17:28:37Z'}
            # data = {'account_hash': '0af634d2-7cfc-4201-ae6f-61bd9ee1ea1d', 'hash': '3e0ad09e-09ae-46e1-988a-c2a80af7f0a8', 'webhook_url': None, 'webhook_type': None, 'callback_id': None, 'prompt': 'Синий океан и зеленая трава', 'type': 'imagine', 'progress': 100, 'status': 'done', 'result': {'url': 'https://cdn.discordapp.com/attachments/1295719054635700308/1299424507055833189/dandangpt______ace5f261-f762-4b0d-9285-25863e674e0c.png?ex=671d26e0&is=671bd560&hm=1d48291c9ac7e4af1e185b82f8f38f95813432f7eb2c1b50b8911d832f406b0a&', 'proxy_url': 'https://media.discordapp.net/attachments/1295719054635700308/1299424507055833189/dandangpt______ace5f261-f762-4b0d-9285-25863e674e0c.png?ex=671d26e0&is=671bd560&hm=1d48291c9ac7e4af1e185b82f8f38f95813432f7eb2c1b50b8911d832f406b0a&', 'filename': 'dandangpt______ace5f261-f762-4b0d-9285-25863e674e0c.png', 'content_type': 'image/png', 'width': 2048, 'height': 2048, 'size': 8655193}, 'next_actions': [{'type': 'upscale', 'choices': [1, 2, 3, 4]}, {'type': 'reroll'}, {'type': 'variation', 'choices': [1, 2, 3, 4]}, {'type': 'seed'}], 'status_reason': None, 'prefilter_result': [], 'created_at': '2024-10-25T17:28:37Z'}
            status = data.get('status')
            progress = await try_to_int(data.get('progress'))
            image_url = data.get('image_url')
            
            return status, progress, image_url
        else:
            return None, None, None
        
    async def variation(self, hash, choice):
        headers = await self.generate_headers()
        data = {
            "hash": hash,
            "choice": choice
        }
        
        async with AsyncClient() as client:
            response = await client.post(f"{self.API_URL}variation", headers=headers, json=data)
        
        if response.status_code == 200:
            data = response.json()
            task_hash = data['hash']
            return task_hash
        
        return None
    
    async def upscale(self, hash, choice):
        headers = await self.generate_headers()
        data = {
            "hash": hash,
            "choice": choice
        }
        
        async with AsyncClient() as client:
            response = await client.post(f"{self.API_URL}upscale", headers=headers, json=data)
        
        if response.status_code == 200:
            data = response.json()
            task_hash = data['hash']
            return task_hash
        
        return None
    
    async def reroll(self, hash):
        headers = await self.generate_headers()
        data = {
            "hash": hash
        }
        
        async with AsyncClient() as client:
            response = await client.post(f"{self.API_URL}reroll", headers=headers, json=data)
        
        if response.status_code == 200:
            data = response.json()
            task_hash = data['hash']
            return task_hash
        
        return None
        
async def try_to_int(value):
    try:
        return int(value)
    except ValueError:
        return value