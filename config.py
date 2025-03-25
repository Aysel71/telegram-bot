# config.py
import os

# Токен бота Telegram
BOT_TOKEN = '7820628749:AAGtbKy-y7KxUtFSs-wnvOIzTu4KNyL4wZA'

# Firebase configuration
# Path to your Firebase service account key file
FIREBASE_CREDENTIALS_PATH = "recsys-4d590-firebase-adminsdk-fbsvc-217f8ac876.json"

# Firebase project details
FIREBASE_PROJECT_ID = "recsys-4d590"
FIREBASE_API_KEY = "AIzaSyBcXNHBA4b_K_Z6i-sfdhBHBb1qDFZrII0"

# Пути к изображениям
# Используем путь к папке img_2, как показано на скриншоте
IMAGES_FOLDER = os.path.join(os.path.dirname(__file__), 'img_2')

# Фиксированное изображение для сравнения
FIXED_IMAGE_PATH = os.path.join(IMAGES_FOLDER, 'afro.jpg')

# Количество изображений для показа в одной сессии
IMAGES_PER_SESSION = 10

# Тайм-аут для ответа пользователя (в секундах)
RESPONSE_TIMEOUT = 30

# Настройки логирования
LOG_LEVEL = "INFO"

# Настройки коллекций Firestore (аналогично таблицам в PostgreSQL)
USERS_COLLECTION = "users"
IMAGES_COLLECTION = "images"
COMPARISONS_COLLECTION = "comparisons"