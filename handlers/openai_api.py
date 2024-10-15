from openai import AsyncOpenAI

from models.dbs.enums import *
from models.dbs.models import *
from models.dbs.orm import Orm


class OpenAI_API:
    SYSTEM_MESSAGE = """
    You are an advanced AI assistant designed to provide accurate, concise, and helpful responses. Your primary goal is to assist users with their queries by providing clear and relevant information. Follow these guidelines to maximize your efficiency:

    1. **Clarity and Conciseness**: Provide clear and concise answers. Avoid unnecessary details unless explicitly requested.
    2. **Accuracy**: Ensure that all information provided is accurate and up-to-date.
    3. **Relevance**: Stick to the topic of the query. Avoid deviating into unrelated subjects.
    4. **Politeness**: Maintain a polite and professional tone at all times.
    5. **Examples and Explanations**: When applicable, provide examples or explanations to clarify complex topics.
    6. **Step-by-Step Instructions**: For procedural queries, provide step-by-step instructions to guide the user.
    7. **Resourcefulness**: If a query requires external resources or references, mention them clearly.
    8. **Adaptability**: Adjust your responses based on the user's level of understanding and context provided in the query.

    Remember, your goal is to be as helpful and efficient as possible. If you are unsure about a query, provide the best possible answer based on the information available.
    """
    
    def __init__(self, user: User, system_message=SYSTEM_MESSAGE):
        self.user = user    
        self.chat_model = user.chat_model
        self.image_model = user.image_model
        self.openai = AsyncOpenAI()
        self.system_message = system_message

    async def __call__(self, query):
        return await self.chatgpt(query)

    async def chatgpt(self, query):
        if await self.validate_request(self.chat_model.name):
            messages = await self.get_chat_messages(query)
            
            response = await self.openai.chat.completions.create(
                model=self.chat_model.value.lower(),
                messages=messages,
                max_tokens=4096
            )
            
            await Orm.add_context_message(self.user, query, "user")            
            await Orm.add_context_message(self.user, response.choices[0].message.content, "assistant")  
            
            await Orm.update_count_of_requests(self.chat_model.name, self.user)
                      
            return response.choices[0].message.content

        return None

    async def get_chat_messages(self, query):
        messages = await Orm.get_context_messages(self.user) + [
            {"role": "system", "content": self.system_message},
            {"role": "user", "content": query}
        ]
        return messages

    async def generate_image(self, query):
        if await self.validate_request(self.image_model.name):
            response = await self.openai.images.generate(
                model=self.image_model.value.lower(),
                prompt=query
            )
            
            await Orm.update_count_of_requests(self.image_model.name, self.user)
            
            return response.data[0].url
        return None
    
    async def validate_request(self, model: str):
        rate_limit = self.user.rate.daily_limit_dict[model]
        if self.user.count_of_requests_dict.get(model) == None:
            await Orm.create_empty_count_of_requests(model, self.user.telegram_id)
            self.user = await Orm.get_user_by_telegram_id(self.user.telegram_id)
        count_of_requests = self.user.count_of_requests_dict[model]
        return count_of_requests < rate_limit