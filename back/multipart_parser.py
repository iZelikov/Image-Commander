import io
import logging
import re
import uuid
import time
from typing import Dict, List, Tuple
from config import MAX_FILE_SIZE_BYTES, FILE_EXTENSIONS, IMAGE_DIR

logger = logging.getLogger(__name__)


class MultipartParser:
    """Класс для парсинга multipart/form-data (честно скопирован у ИИ)"""

    def __init__(self, headers: Dict[str, str], input_stream: io.BytesIO,
                 content_length: int, max_size: int = MAX_FILE_SIZE_BYTES):
        self.headers = headers
        self.input_stream = input_stream
        self.content_length = content_length
        self.max_size = max_size
        self.boundary = None
        self.fields = {}
        self.files = {}
        logger.debug(f"MultipartParser initialized with content_length: {content_length}, max_size: {max_size}")

    def parse(self) -> Tuple[Dict, Dict]:
        """Парсинг multipart данных"""
        content_type = self.headers.get('Content-Type', '')

        if not content_type.startswith('multipart/form-data'):
            error_msg = 'Expected multipart/form-data content type'
            logger.error(error_msg)
            raise ValueError(error_msg)

        # Извлекаем boundary из заголовка
        boundary_match = re.search(r'boundary=([^;]+)', content_type)
        if not boundary_match:
            error_msg = 'No boundary found in Content-Type header'
            logger.error(error_msg)
            raise ValueError(error_msg)

        self.boundary = '--' + boundary_match.group(1).strip('"')
        logger.debug(f"Boundary extracted: {self.boundary}")

        # Читаем все данные
        raw_data = self.input_stream.read(self.content_length)
        logger.debug(f"Read {len(raw_data)} bytes of raw data")

        # Разделяем на части по boundary
        parts = raw_data.split(self.boundary.encode())

        logger.debug(f"Found {len(parts)} parts in multipart data")
        for i, part in enumerate(parts):
            if not part.strip() or part.strip() == b'--':
                continue  # Пропускаем пустые части и завершающую boundary

            logger.debug(f"Parsing part {i}")
            self._parse_part(part.strip())

        logger.info(
            f"Multipart parsing completed: {len(self.fields)} fields, {sum(len(f) for f in self.files.values())} files")
        return self.fields, self.files

    def _parse_part(self, part_data: bytes):
        """Парсинг одной части multipart данных"""
        # Разделяем заголовки и тело
        headers_end = part_data.find(b'\r\n\r\n')
        if headers_end == -1:
            logger.warning("Part doesn't contain proper headers separator")
            return

        headers_raw = part_data[:headers_end]
        body = part_data[headers_end + 4:]  # +4 для пропуска \r\n\r\n

        # Парсим заголовки
        headers = self._parse_headers(headers_raw)

        # Извлекаем имя поля и имя файла из Content-Disposition
        content_disposition = headers.get('Content-Disposition', '')

        # Ищем имя поля и имя файла
        name_match = re.search(r'name="([^"]+)"', content_disposition)
        if not name_match:
            logger.warning("No 'name' found in Content-Disposition header")
            return

        field_name = name_match.group(1)

        # Проверяем, это файл или обычное поле
        filename_match = re.search(r'filename="([^"]+)"', content_disposition)

        if filename_match:
            # Это файл
            filename = filename_match.group(1)
            logger.debug(f"Found file field: {field_name}, filename: {filename}")

            # Проверяем размер
            if len(body) > self.max_size:
                error_msg = f'File {filename} exceeds maximum size of {self.max_size} bytes'
                logger.error(error_msg)
                raise ValueError(error_msg)

            # Сохраняем информацию о файле
            self.files.setdefault(field_name, []).append({
                'filename': filename,
                'data': body,
                'content_type': headers.get('Content-Type', 'application/octet-stream'),
                'size': len(body)
            })
            logger.debug(f"Added file {filename} to field {field_name}, size: {len(body)} bytes")
        else:
            # Это обычное текстовое поле
            field_value = body.decode('utf-8')
            self.fields[field_name] = field_value
            logger.debug(f"Added text field: {field_name} = {field_value[:50]}...")

    def _parse_headers(self, headers_raw: bytes) -> Dict[str, str]:
        """Парсинг заголовков из байтов в словарь"""
        headers = {}
        lines = headers_raw.decode('utf-8', errors='ignore').split('\r\n')

        for line in lines:
            if ': ' in line:
                key, value = line.split(': ', 1)
                headers[key] = value

        logger.debug(f"Parsed headers: {list(headers.keys())}")
        return headers


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
            ext = 'jpg'  # fallback

    new_filename = f"{timestamp}_{unique_id}.{ext}"
    filepath = IMAGE_DIR / new_filename

    logger.debug(f"Saving file: {original_filename} -> {new_filename} ({len(file_data)} bytes)")

    # Сохраняем файл
    with open(filepath, 'wb') as f:
        f.write(file_data)

    logger.info(f"File saved successfully: {new_filename}")
    return new_filename