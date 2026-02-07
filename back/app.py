import logging
import socketserver

from config import IMAGE_DIR, HOST, PORT, DEBUG, BACKUP_DIR
from http_handler import ImageRequestHandler
from db import init_tables

logger = logging.getLogger(__name__)

def run_server():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    init_tables()

    IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    handler = ImageRequestHandler
    httpd = socketserver.TCPServer((HOST, PORT), handler)

    logger.info(f"Server running on {HOST}:{PORT}")
    logger.info(f"Image directory: {IMAGE_DIR}")
    logger.info(f"Debug mode: {DEBUG}")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info("\nServer stopped")
        httpd.server_close()


if __name__ == "__main__":

    run_server()