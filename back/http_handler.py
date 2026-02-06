import http.server
import json
import logging
import urllib.parse
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent))
logger = logging.getLogger(__name__)

from config import DEBUG, IMAGE_DIR
from db import get_images_metadata, save_metadata, delete_metadata
from multipart_parser import MultipartParser, validate_image_file, save_uploaded_file


class ImageRequestHandler(http.server.BaseHTTPRequestHandler):

    def _set_headers(self, status_code=200, content_type='application/json'):
        self.send_response(status_code)
        self.send_header('Content-type', content_type)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_OPTIONS(self):
        self._set_headers(200)

    def do_GET(self):
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path

        if path == '/get_images/' or path == '/get_images':
            try:

                query_params = urllib.parse.parse_qs(parsed_path.query)
                page = int(query_params.get('page', [1])[0])
                page_size = int(query_params.get('page_size', [10])[0])

                images = get_images_metadata(page=page, page_size=page_size)

                result = []
                for img in images:
                    result.append({
                        'id': img[0],
                        'filename': img[1],
                        'original_filename': img[2],
                        'size': img[3],
                        'upload_time': img[4].isoformat() if img[4] else None,
                        'file_type': img[5]
                    })

                self._set_headers(200)
                self.wfile.write(json.dumps(result).encode())

            except Exception as e:
                self._set_headers(500)
                error_msg = {'error': str(e)}
                self.wfile.write(json.dumps(error_msg).encode())

        elif path == '/health/' or path == '/health':
            self._set_headers(200)
            response = {'status': 'ok', 'service': 'image-commander'}
            self.wfile.write(json.dumps(response).encode())

        else:
            self._set_headers(404)
            self.wfile.write(json.dumps({'error': 'Not found'}).encode())

    def do_POST(self):
        """Обработка POST запросов для загрузки файлов"""
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path

        if path == '/upload/' or path == '/upload':
            try:
                content_length = int(self.headers.get('Content-Length', 0))

                if content_length == 0:
                    self._set_headers(400)
                    self.wfile.write(json.dumps({'error': 'No data provided'}).encode())
                    return

                parser = MultipartParser(
                    headers=dict(self.headers),
                    input_stream=self.rfile,
                    content_length=content_length
                )

                fields, files = parser.parse()

                uploaded_files = []
                errors = []

                for file_key in files:
                    for file_info in files[file_key]:
                        filename = file_info['filename']
                        file_data = file_info['data']

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

                            except Exception as e:
                                errors.append(f"Error saving {filename}: {str(e)}")
                        else:
                            errors.append(f"File {filename}: {', '.join(validation['errors'])}")

                if uploaded_files:
                    response = {
                        'success': True,
                        'message': f'Successfully uploaded {len(uploaded_files)} file(s)',
                        'uploaded': uploaded_files,
                        'errors': errors if errors else None
                    }
                    self._set_headers(200)
                else:
                    response = {
                        'success': False,
                        'message': 'No files were uploaded',
                        'errors': errors
                    }
                    self._set_headers(400)

                self.wfile.write(json.dumps(response).encode())

            except Exception as e:
                self._set_headers(500)
                error_msg = {'error': f'Server error: {str(e)}'}
                self.wfile.write(json.dumps(error_msg).encode())

        else:
            self._set_headers(404)
            self.wfile.write(json.dumps({'error': 'Not found'}).encode())

    def do_DELETE(self):
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path

        if path.startswith('/delete/'):
            try:
                filename = path.split('/delete/')[-1]

                if not filename:
                    self._set_headers(400)
                    self.wfile.write(json.dumps({'error': 'Filename required'}).encode())
                    return

                filepath = IMAGE_DIR / filename
                if filepath.exists():
                    filepath.unlink()

                delete_metadata(filename)

                response = {
                    'success': True,
                    'message': f'File {filename} deleted successfully'
                }
                self._set_headers(200)
                self.wfile.write(json.dumps(response).encode())

            except Exception as e:
                self._set_headers(500)
                error_msg = {'error': str(e)}
                self.wfile.write(json.dumps(error_msg).encode())

        else:
            self._set_headers(404)
            self.wfile.write(json.dumps({'error': 'Not found'}).encode())

    def log_message(self, format, *args):
        if DEBUG:
            super().log_message(format, *args)
