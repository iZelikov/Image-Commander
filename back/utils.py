import logging
import uuid

from config import MAX_FILE_SIZE_BYTES, FILE_EXTENSIONS, IMAGE_DIR

logger = logging.getLogger(__name__)


def save_image(filename: str, post_data: bytes):
    file_path = IMAGE_DIR / filename
    with open(file_path, 'wb') as f:
        f.write(post_data)


def delete_image(filename):
    file_path = IMAGE_DIR / filename
    if file_path.exists():
        file_path.unlink()
        logger.info(f"File '{file_path}' has been deleted.")
    else:
        logger.error(f"File '{file_path}' does not exist.")


def validate_image(post_data, ext):
    if len(post_data) > MAX_FILE_SIZE_BYTES:
        raise Exception('File too large')
    if ext not in FILE_EXTENSIONS:
        raise Exception('Not allowed extension')


def generate_unique_name(filename) -> str:
    return f'{filename}_{uuid.uuid4()}'