import http.server
import json
import logging
import urllib.parse
from pathlib import Path

from config import DEBUG, IMAGE_DIR, PREVIEW_DIR
from db import get_images_metadata, save_metadata, delete_metadata, get_images_count
from multipart_parser import MultipartParser
from helpers import validate_image_file, save_uploaded_file

logger = logging.getLogger(__name__)


class ImageRequestHandler(http.server.BaseHTTPRequestHandler):

    def _set_headers(self, status_code=200, content_type='application/json'):
        self.send_response(status_code)
        self.send_header('Content-type', content_type)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_OPTIONS(self):
        logger.debug(f"OPTIONS request for {self.path}")
        self._set_headers(200)

    def do_GET(self):
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path
        logger.info(f"GET request for {path}")

        if path.startswith('/get_images'):
            try:
                query_params = urllib.parse.parse_qs(parsed_path.query)
                page = int(query_params.get('page', [1])[0])
                page_size = int(query_params.get('size', [10])[0])
                logger.debug(f"Getting images - page: {page}, page_size: {page_size}")

                images = get_images_metadata(page=page, page_size=page_size)
                images_count = get_images_count()
                files = []
                for img in images:
                    files.append({
                        'id': img[0],
                        'filename': img[1],
                        'original_filename': img[2],
                        'size': img[3],
                        'upload_time': img[4].isoformat() if img[4] else None,
                        'file_type': img[5],
                        'link': f'{IMAGE_DIR}/{img[1]}',
                        'preview': f'{PREVIEW_DIR}/{img[1]}'
                    })
                result = {'files': files, 'total': images_count}
                logger.info(f"Returning {len(files)} images (total: {images_count})")
                self._set_headers(200)
                self.wfile.write(json.dumps(result).encode())

            except Exception as e:
                logger.error(f"Error processing GET /get_images: {e}", exc_info=True)
                self._set_headers(500)
                error_msg = {'error': str(e)}
                self.wfile.write(json.dumps(error_msg).encode())

        elif path == '/health/' or path == '/health':
            logger.debug("Health check requested")
            self._set_headers(200)
            response = {'status': 'ok', 'service': 'image-commander'}
            self.wfile.write(json.dumps(response).encode())

        else:
            logger.warning(f"GET request for unknown path: {path}")
            self._set_headers(404)
            self.wfile.write(json.dumps({'error': 'Not found'}).encode())

    def do_POST(self):
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path
        logger.info(f"POST request for {path}")

        if path.startswith('/upload'):
            try:
                content_length = int(self.headers.get('Content-Length', 0))
                logger.debug(f"Upload request content length: {content_length} bytes")

                if content_length == 0:
                    logger.warning("Upload request with no data")
                    self._set_headers(400)
                    self.wfile.write(json.dumps({'error': 'No data provided'}).encode())
                    return

                parser = MultipartParser(
                    headers=dict(self.headers),
                    input_stream=self.rfile,
                    content_length=content_length
                )

                fields, files = parser.parse()
                logger.debug(f"Parsed upload: {len(fields)} fields, {sum(len(f) for f in files.values())} files")

                uploaded_files = []
                errors = []

                for file_key in files:
                    for file_info in files[file_key]:
                        filename = file_info['filename']
                        file_data = file_info['data']
                        logger.debug(f"Processing file: {filename}, size: {len(file_data)} bytes")

                        validation = validate_image_file(file_data, filename)

                        if validation['valid']:
                            try:
                                new_filename = save_uploaded_file(file_data, filename)
                                save_metadata(
                                    filename=new_filename,
                                    original_name=filename,
                                    size=validation['size'],
                                    file_type=validation['file_type']
                                )

                                uploaded_files.append({
                                    'original_name': filename,
                                    'saved_name': new_filename,
                                    'size': validation['size'],
                                    'url': f'/images/{new_filename}'
                                })
                                logger.info(f"Successfully uploaded file: {filename} -> {new_filename}")

                            except Exception as e:
                                error_msg = f"Error saving {filename}: {str(e)}"
                                logger.error(error_msg, exc_info=True)
                                errors.append(error_msg)
                        else:
                            error_msg = f"File {filename}: {', '.join(validation['errors'])}"
                            logger.warning(error_msg)
                            errors.append(error_msg)

                if uploaded_files:
                    response = {
                        'success': True,
                        'message': f'Successfully uploaded {len(uploaded_files)} file(s)',
                        'uploaded': uploaded_files,
                        'errors': errors if errors else None
                    }
                    logger.info(f"Upload completed successfully: {len(uploaded_files)} files uploaded")
                    self._set_headers(200)
                else:
                    response = {
                        'success': False,
                        'message': 'No files were uploaded',
                        'errors': errors
                    }
                    logger.warning(f"Upload failed: {errors}")
                    self._set_headers(400)

                self.wfile.write(json.dumps(response).encode())

            except Exception as e:
                logger.error(f"Server error during upload: {e}", exc_info=True)
                self._set_headers(500)
                error_msg = {'error': f'Server error: {str(e)}'}
                self.wfile.write(json.dumps(error_msg).encode())

        else:
            logger.warning(f"POST request for unknown path: {path}")
            self._set_headers(404)
            self.wfile.write(json.dumps({'error': 'Not found'}).encode())

    def do_DELETE(self):
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path
        logger.info(f"DELETE request for {path}")

        if path.startswith('/delete/'):
            try:
                filename = path.split('/delete/')[-1]
                logger.debug(f"Delete request for file: {filename}")

                if not filename:
                    logger.warning("Delete request without filename")
                    self._set_headers(400)
                    self.wfile.write(json.dumps({'error': 'Filename required'}).encode())
                    return

                # Удаляем оригинальный файл
                filepath = IMAGE_DIR / filename
                if filepath.exists():
                    filepath.unlink()
                    logger.info(f"Deleted file from disk: {filename}")
                else:
                    logger.warning(f"File not found on disk: {filename}")

                # Удаляем превью (если существует)
                preview_path = PREVIEW_DIR / (Path(filename).stem + '.jpg')
                if preview_path.exists():
                    preview_path.unlink()
                    logger.info(f"Deleted preview from disk: {preview_path.name}")

                # Удаляем метаданные из БД
                delete_metadata(filename)

                response = {
                    'success': True,
                    'message': f'File {filename} deleted successfully'
                }
                logger.info(f"Successfully deleted file: {filename}")
                self._set_headers(200)
                self.wfile.write(json.dumps(response).encode())

            except Exception as e:
                logger.error(f"Error deleting file: {e}", exc_info=True)
                self._set_headers(500)
                error_msg = {'error': str(e)}
                self.wfile.write(json.dumps(error_msg).encode())

        else:
            logger.warning(f"DELETE request for unknown path: {path}")
            self._set_headers(404)
            self.wfile.write(json.dumps({'error': 'Not found'}).encode())

    def log_message(self, format, *args):
        if DEBUG:
            logger.debug(f"HTTP: {format % args}")