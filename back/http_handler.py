import http
import json
import logging
import urllib
from urllib.parse import parse_qs

from db import (get_images_metadata,
                get_image_metadata,
                delete_metadata,
                save_metadata)
from utils import save_image, validate_image, generate_unique_name, delete_image

logger = logging.getLogger(__name__)


class RequestHandler(http.server.BaseHTTPRequestHandler):
    server_version = "ImageCommander/0.1"

    def do_GET(self):
        """Handle GET requests."""
        parsed_path = urllib.parse.urlparse(self.path)
        logger.info(f"GET request, path = {parsed_path}")

        page = int(parse_qs(parsed_path.query).get('page', [1])[0])
        page_size = int(parse_qs(parsed_path.query).get('page_size', [10])[0])
        logger.info(f'page, page_size: {page}, {page_size}')

        if parsed_path.path == "/get_images/":
            images = get_images_metadata(page, page_size)
            images = [
                {
                    'filename': i[1],
                    'original_filename': i[2],
                    'size': i[3],
                    'date': i[4].strftime("%Y-%m-%d %H:%M:%S"),
                    'type': i[5]
                }
                for i in images
            ]

            self.send_json(images)
        else:
            self.send_json({"error": "Not found"}, 404)

    def do_POST(self):
        """Handle POST requests."""
        parsed_path = urllib.parse.urlparse(self.path)
        logger.info(f"POST request, path = {parsed_path.path}")

        if parsed_path.path == '/upload/':
            pass

    def do_DELETE(self):
        """Handle DELETE requests."""
        parsed_path = urllib.parse.urlparse(self.path)
        logger.info(f"DELETE request, path = {parsed_path.path}")

        if self.path.startswith("/delete_image/"):
            filename = parsed_path.path.split("/")[2]
            try:
                delete_metadata(filename)
                delete_image(filename)
                self.send_json({}, 204)
            except Exception as e:
                self.send_json({"error": str(e)}, 404)
        else:
            self.send_json({"error": "Not found"}, 404)

    def send_json(self, data: dict | list, status_code: int = 200):
        """Send JSON response."""
        logger.info(f"Sending JSON response: {data}")
        self.send_response(status_code)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode("utf-8"))
