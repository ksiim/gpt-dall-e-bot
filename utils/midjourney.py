from config import ACCOUNT_HASH, USERAPI_UI_API_KEY, USERAPI_UI_URL, OPENAI_API_KEY
from httpx import AsyncClient

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
            result = response.json()
            task_hash = result['hash']
            return task_hash
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


    async def check_image_url(self, task_hash):
        """Проверка статуса задачи и получение URL изображения по хэшу задачи"""
        headers = await self.generate_headers()
        
        status_url = f"{self.API_URL}status?hash={task_hash}"
        
        async with AsyncClient() as client:
            response = await client.get(status_url, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            return result
            if result and result['status'] == 'done' and 'result' in result and 'url' in result['result']:
                image_url = result['result']['url']
            else:
                pass
        else:
            pass