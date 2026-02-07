from dotenv import load_dotenv
from pathlib import Path
import os

load_dotenv()

DB_CONFIG = {
    "host": os.getenv("POSTGRES_HOST"),
    "port": os.getenv("POSTGRES_PORT"),
    "user": os.getenv("POSTGRES_USER"),
    "password": os.getenv("POSTGRES_PASSWORD"),
    "dbname": os.getenv("POSTGRES_DB")
}

FILE_EXTENSIONS = ["jpg", "jpeg", "png", "gif", 'webp']
MAX_FILE_SIZE_MB = 5
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

# Максимальный размер всего запроса (может содержать несколько файлов)
MAX_REQUEST_SIZE_MB = 50
MAX_REQUEST_SIZE_BYTES = MAX_REQUEST_SIZE_MB * 1024 * 1024

HOST, PORT = ('0.0.0.0', 8000)
DEBUG = True
BASE_DIR = PATH = Path(__file__).parent.parent
IMAGE_DIR = BASE_DIR / "images"
BACKUP_DIR = BASE_DIR / "backup"

# Таймауты для загрузки файлов
UPLOAD_TIMEOUT_SECONDS = 300  # 5 минут