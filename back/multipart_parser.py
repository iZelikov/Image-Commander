import io
import logging
import re
from typing import Dict, Tuple
from config import MAX_FILE_SIZE_BYTES

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


