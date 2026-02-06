import http.server
import logging

from config import HOST, PORT
from http_handler import RequestHandler
from db import init_tables


def run_server():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    init_tables()

    httpd = http.server.HTTPServer((HOST, PORT), RequestHandler)
    logging.info(f'Starting httpd server on {HOST}:{PORT}...\n')
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
    logging.info('Stopping httpd server.\n')


if __name__ == "__main__":

    run_server()