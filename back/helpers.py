import time
import uuid
from pathlib import Path
from typing import Dict
import shutil
import tempfile

from config import FILE_EXTENSIONS, MAX_FILE_SIZE_BYTES, IMAGE_DIR, PREVIEW_DIR, PREVIEW_SIZE, PREVIEW_QUALITY
from multipart_parser import logger
from PIL import Image, ImageOps


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


# def convert_to_green_scale(image):
#     """Делаем пикселявое зелёное изображение (и получается фигня)"""
#     # Преобразуем в оттенки серого
#     grayscale = image.convert('L')
#
#     # Создаем нулевые каналы для красного и синего
#     zero_channel = Image.new('L', grayscale.size, 0)
#
#     # Объединяем каналы: R=0, G=grayscale, B=0
#     img = Image.merge('RGB', (zero_channel, grayscale, zero_channel))
#     posterized_img = ImageOps.posterize(img, 3)
#     # pixelated_img = posterized_img.resize((64, 64), Image.Resampling.BICUBIC)
#     # posterized_img = pixelated_img.resize(img.size, Image.Resampling.BOX)
#     return posterized_img


def prepare_upload(file_data: bytes, original_filename: str):
    """
    Сохраняет файл и его превью во временную директорию.
    Возвращает (temp_original_path, temp_preview_path, final_filename)
    """
    # Генерируем уникальное имя финального файла
    timestamp = int(time.time())
    unique_id = str(uuid.uuid4())[:8]

    # Определяем расширение
    ext = original_filename.split('.')[-1].lower() if '.' in original_filename else ''
    if ext not in FILE_EXTENSIONS:
        # Определяем по сигнатуре
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

    final_filename = f"{timestamp}_{unique_id}.{ext}"

    # Уникальное имя для временного preview
    preview_filename = Path(final_filename).stem + '_preview.jpg'

    temp_dir = IMAGE_DIR / ".upload_tmp"
    temp_dir.mkdir(parents=True, exist_ok=True)

    temp_original_path = temp_dir / final_filename
    temp_preview_path = temp_dir / preview_filename

    # Финальные пути (куда перемещать после успешной БД)
    final_original = IMAGE_DIR / final_filename
    final_preview = PREVIEW_DIR / (Path(final_filename).stem + '.jpg')

    # Сохраняем оригинал и preview во временную папку
    with open(temp_original_path, 'wb') as f:
        f.write(file_data)
    _create_preview_to_path(temp_original_path, temp_preview_path,
                            size=PREVIEW_SIZE, quality=PREVIEW_QUALITY)

    return temp_original_path, temp_preview_path, final_original, final_preview


def _create_preview_to_path(src_path: Path, dst_path: Path, size: int, quality: int):
    """Создаёт превью из src_path и сохраняет в dst_path (JPEG)."""
    try:
        with Image.open(src_path) as img:
            # Конвертируем в RGB при необходимости
            if img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (0, 0, 0))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')

            img.thumbnail((size, size))
            img.save(dst_path, 'JPEG', quality=quality)
            logger.info(f"Preview created: {dst_path}")
    except Exception as e:
        logger.error(f"Failed to create preview from {src_path}: {e}", exc_info=True)
        raise


def commit_upload(temp_orig: Path, temp_preview: Path, final_orig: Path, final_preview: Path):
    """Перемещает временные файлы в финальные директории."""
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
    shutil.move(str(temp_orig), str(final_orig))
    shutil.move(str(temp_preview), str(final_preview))
    logger.info(f"Committed upload: {final_orig.name}")


def rollback_upload(temp_orig: Path, temp_preview: Path):
    """Удаляет временные файлы при ошибке."""
    for p in (temp_orig, temp_preview):
        if p.exists():
            p.unlink()
    logger.info("Rolled back upload")
