import logging
import socketserver

from config import IMAGE_DIR, HOST, PORT, DEBUG, BACKUP_DIR, LOG_DIR
from http_handler import ImageRequestHandler
from db import init_tables

logger = logging.getLogger(__name__)


def setup_logging():
    """Настройка логирования в файл и консоль"""
    # Создаем директорию для логов, если она не существует
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    # Создаем форматтер
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Обработчик для записи в файл
    file_handler = logging.FileHandler(LOG_DIR / 'app.log', encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)

    # Обработчик для вывода в консоль
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO if not DEBUG else logging.DEBUG)
    console_handler.setFormatter(formatter)

    # Настраиваем корневой логгер
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)


def run_server():
    setup_logging()

    logger.info("Initializing database tables...")
    init_tables()

    logger.info(f"Creating directories if they don't exist: {IMAGE_DIR}, {BACKUP_DIR}")
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    handler = ImageRequestHandler
    httpd = socketserver.TCPServer((HOST, PORT), handler)

    logger.info(f"Server starting on {HOST}:{PORT}")
    logger.info(f"Image directory: {IMAGE_DIR}")
    logger.info(f"Debug mode: {DEBUG}")
    logger.info(f"Log directory: {LOG_DIR}")

    try:
        logger.info("Server is ready to accept connections")
        httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
        httpd.server_close()
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    run_server()