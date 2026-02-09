import time
import uuid
from pathlib import Path
from typing import Dict

from config import FILE_EXTENSIONS, MAX_FILE_SIZE_BYTES, IMAGE_DIR, PREVIEW_DIR, PREVIEW_SIZE, PREVIEW_QUALITY
from multipart_parser import logger
from PIL import Image

def validate_image_file(file_data: bytes, filename: str) -> Dict:
    """Валидация загружаемого изображения"""
    errors = []
    logger.debug(f"Validating file: {filename}, size: {len(file_data)} bytes")

    # Проверка расширения
    ext = filename.lower().split('.')[-1] if '.' in filename else ''
    if ext not in FILE_EXTENSIONS:
        error_msg = f'Invalid file extension: {ext}. Allowed: {FILE_EXTENSIONS}'
        logger.warning(error_msg)
        errors.append(error_msg)

    # Проверка размера
    if len(file_data) > MAX_FILE_SIZE_BYTES:
        error_msg = f'File size ({len(file_data)} bytes) exceeds limit ({MAX_FILE_SIZE_BYTES} bytes)'
        logger.warning(error_msg)
        errors.append(error_msg)

    # Проверка сигнатур (magic numbers) изображений
    # JPEG: FF D8 FF
    # PNG: 89 50 4E 47 0D 0A 1A 0A
    # GIF: GIF87a или GIF89a
    # WebP: RIFF....WEBP

    if len(file_data) >= 3:
        # JPEG
        if file_data[:3] == b'\xff\xd8\xff':
            file_type = 'jpeg'
            logger.debug(f"Detected JPEG file: {filename}")
        # PNG (8 байт сигнатуры)
        elif len(file_data) >= 8 and file_data[:8] == b'\x89PNG\r\n\x1a\n':
            file_type = 'png'
            logger.debug(f"Detected PNG file: {filename}")
        # GIF
        elif len(file_data) >= 6 and file_data[:6] in (b'GIF87a', b'GIF89a'):
            file_type = 'gif'
            logger.debug(f"Detected GIF file: {filename}")
        # WebP
        elif len(file_data) >= 12 and file_data[:4] == b'RIFF' and file_data[8:12] == b'WEBP':
            file_type = 'webp'
            logger.debug(f"Detected WebP file: {filename}")
        else:
            error_msg = 'File is not a valid image (unknown format)'
            logger.warning(error_msg)
            errors.append(error_msg)
            file_type = 'unknown'
    else:
        error_msg = 'File is too small to be a valid image'
        logger.warning(error_msg)
        errors.append(error_msg)
        file_type = 'unknown'

    result = {
        'valid': len(errors) == 0,
        'errors': errors,
        'file_type': file_type,
        'size': len(file_data)
    }

    if result['valid']:
        logger.info(f"File validation successful: {filename}, type: {file_type}, size: {len(file_data)} bytes")
    else:
        logger.warning(f"File validation failed for {filename}: {errors}")

    return result


def save_uploaded_file(file_data: bytes, original_filename: str) -> str:
    """Сохранение загруженного файла с уникальным именем"""
    # Генерируем уникальное имя файла
    timestamp = int(time.time())
    unique_id = str(uuid.uuid4())[:8]

    # Сохраняем оригинальное расширение, если оно допустимо
    ext = original_filename.split('.')[-1].lower() if '.' in original_filename else ''
    if ext not in FILE_EXTENSIONS:
        # Определяем расширение по сигнатуре
        if file_data[:3] == b'\xff\xd8\xff':
            ext = 'jpg'
        elif len(file_data) >= 8 and file_data[:8] == b'\x89PNG\r\n\x1a\n':
            ext = 'png'
        elif len(file_data) >= 6 and file_data[:6] in (b'GIF87a', b'GIF89a'):
            ext = 'gif'
        elif len(file_data) >= 12 and file_data[:4] == b'RIFF' and file_data[8:12] == b'WEBP':
            ext = 'webp'
        else:
            ext = 'jpg'

    new_filename = f"{timestamp}_{unique_id}.{ext}"
    filepath = IMAGE_DIR / new_filename

    logger.debug(f"Saving file: {original_filename} -> {new_filename} ({len(file_data)} bytes)")

    # Сохраняем файл
    with open(filepath, 'wb') as f:
        f.write(file_data)

    logger.info(f"File saved successfully: {new_filename}")

    # Создаем превью
    create_preview(filepath, new_filename, size=PREVIEW_SIZE, quality=PREVIEW_QUALITY)

    return new_filename


def create_preview(image_path: Path, filename: str, size=300, quality=60):
    """Создание превью изображения"""

    try:
        # Создаем папку для превью, если её нет
        preview_dir = PREVIEW_DIR
        preview_dir.mkdir(parents=True, exist_ok=True)

        # Открываем изображение
        with Image.open(image_path) as img:
            # Конвертируем в RGB если нужно (для PNG с прозрачностью)
            if img.mode in ('RGBA', 'LA', 'P'):
                # Создаем черный фон для прозрачных изображений
                background = Image.new('RGB', img.size, (0, 0, 0))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')

            # Создаем превью (максимальный размер 300x300, сохраняя пропорции)
            img.thumbnail((size, size))

            # Сохраняем превью с тем же именем (всегда в формате JPEG для экономии места)
            preview_filename = Path(filename).stem + '.jpg'
            preview_path = preview_dir / preview_filename

            # Сохраняем с хорошим качеством
            img.save(preview_path, 'JPEG', quality=quality)

            logger.info(f"Preview created: {preview_path}")

    except Exception as e:
        logger.error(f"Failed to create preview for {filename}: {e}", exc_info=True)
