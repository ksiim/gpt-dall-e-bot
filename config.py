from dotenv import load_dotenv
import os


load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
DB_NAME = os.getenv('DB_NAME')
DB_DIR = os.path.join(os.getcwd(), DB_NAME)
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_HOST = os.getenv('DB_HOST')
DATABASE_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"
SYNC_DATABASE_URL = f"postgresql+psycopg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"
PAYMENTS_TOKEN = os.getenv('PAYMENTS_TOKEN')
YOOKASSA_SHOP_ID = os.getenv('YOOKASSA_SHOP_ID')
YOOKASSA_SECRET_KEY = os.getenv('YOOKASSA_SECRET_KEY')
USERAPI_UI_API_KEY = os.getenv('USERAPI_UI_API_KEY')
ACCOUNT_HASH = os.getenv('ACCOUNT_HASH')
USERAPI_UI_URL = os.getenv('USERAPI_UI_URL')
