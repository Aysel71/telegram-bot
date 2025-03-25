# config.py
import os
from dotenv import load_dotenv

# Load environment variables from .env file if present
load_dotenv()

# Токен бота Telegram
BOT_TOKEN = os.getenv('BOT_TOKEN')

# Firebase configuration
# Path to your Firebase service account key file
FIREBASE_CREDENTIALS_PATH = os.getenv('FIREBASE_CREDENTIALS_PATH', "recsys-4d590-firebase-adminsdk-fbsvc-217f8ac876.json")

# Firebase project details
FIREBASE_PROJECT_ID = os.getenv('FIREBASE_PROJECT_ID', "recsys-4d590")
FIREBASE_API_KEY = os.getenv('FIREBASE_API_KEY')

# Пути к изображениям
# Используем путь к папке img_2
IMAGES_FOLDER = os.getenv('IMAGES_FOLDER', os.path.join(os.path.dirname(__file__), 'img_2'))

# Фиксированное изображение для сравнения
FIXED_IMAGE_PATH = os.path.join(IMAGES_FOLDER, os.getenv('FIXED_IMAGE_NAME', 'afro.jpg'))

# Количество изображений для показа в одной сессии
IMAGES_PER_SESSION = int(os.getenv('IMAGES_PER_SESSION', 10))

# Тайм-аут для ответа пользователя (в секундах)
RESPONSE_TIMEOUT = int(os.getenv('RESPONSE_TIMEOUT', 30))

# Настройки логирования
LOG_LEVEL = os.getenv('LOG_LEVEL', "INFO")

# Настройки коллекций Firestore
USERS_COLLECTION = os.getenv('USERS_COLLECTION', "users")
IMAGES_COLLECTION = os.getenv('IMAGES_COLLECTION', "images")
COMPARISONS_COLLECTION = os.getenv('COMPARISONS_COLLECTION', "comparisons")# config.py
import os
from dotenv import load_dotenv

# Load environment variables from .env file if present
load_dotenv()

# Токен бота Telegram
BOT_TOKEN = os.getenv('BOT_TOKEN')

# Firebase configuration
# Path to your Firebase service account key file
FIREBASE_CREDENTIALS_PATH = os.getenv('FIREBASE_CREDENTIALS_PATH', "recsys-4d590-firebase-adminsdk-fbsvc-217f8ac876.json")

# Firebase project details
FIREBASE_PROJECT_ID = os.getenv('FIREBASE_PROJECT_ID', "recsys-4d590")
FIREBASE_API_KEY = os.getenv('FIREBASE_API_KEY')

# Пути к изображениям
# Используем путь к папке img_2
IMAGES_FOLDER = os.getenv('IMAGES_FOLDER', os.path.join(os.path.dirname(__file__), 'img_2'))

# Фиксированное изображение для сравнения
FIXED_IMAGE_PATH = os.path.join(IMAGES_FOLDER, os.getenv('FIXED_IMAGE_NAME', 'afro.jpg'))

# Количество изображений для показа в одной сессии
IMAGES_PER_SESSION = int(os.getenv('IMAGES_PER_SESSION', 10))

# Тайм-аут для ответа пользователя (в секундах)
RESPONSE_TIMEOUT = int(os.getenv('RESPONSE_TIMEOUT', 30))

# Настройки логирования
LOG_LEVEL = os.getenv('LOG_LEVEL', "INFO")

# Настройки коллекций Firestore
USERS_COLLECTION = os.getenv('USERS_COLLECTION', "users")
IMAGES_COLLECTION = os.getenv('IMAGES_COLLECTION', "images")
COMPARISONS_COLLECTION = os.getenv('COMPARISONS_COLLECTION', "comparisons")
