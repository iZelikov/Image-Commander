import logging
import psycopg
from psycopg import Connection

from config import DB_CONFIG

logger = logging.getLogger(__name__)

def get_db_connection() -> Connection:
    try:
        logger.debug(f"Attempting to connect to database with config: {DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['dbname']}")
        db = psycopg.connect(**DB_CONFIG)
        logger.info("Database connection established successfully")
        return db
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}", exc_info=True)
        raise

def execute_query(query, log_success, log_fail, params=None):
    try:
        logger.debug(f"Executing query: {query[:100]}... with params: {params}")
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, params)
                conn.commit()
                logger.info(log_success)
    except Exception as e:
        logger.error(f"{log_fail}: {e}", exc_info=True)
        raise

def fetch_query(query, params=None):
    try:
        logger.debug(f"Fetching query: {query[:100]}... with params: {params}")
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, params)
                result = cur.fetchall()
                logger.info(f"Query executed successfully. Rows returned: {len(result)}")
                logger.debug(f"Query result: {result}")
                return result
    except Exception as e:
        logger.error(f'Failed to execute query: {e}', exc_info=True)
        raise

def init_tables():
    logger.info("Initializing database tables...")
    query = """CREATE TABLE IF NOT EXISTS images (
                          id SERIAL PRIMARY KEY,
                          filename TEXT NOT NULL,
                          original_name TEXT NOT NULL,
                          size INTEGER NOT NULL,
                          upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                          file_type TEXT NOT NULL
                        );"""
    log_success = "Tables initialized successfully or already exists"
    log_fail = "Failed to initialize tables"

    execute_query(query, log_success, log_fail)

def save_metadata(filename, original_name, size, file_type):
    logger.info(f"Saving metadata for file: {filename} (original: {original_name}, size: {size}, type: {file_type})")
    query = """
        INSERT INTO images (filename, original_name, size, file_type)
        VALUES (%s, %s, %s, %s)
    """
    log_success = f"Metadata saved successfully for {filename}"
    log_fail = "Failed to save metadata"
    execute_query(query, log_success, log_fail, (filename, original_name, size, file_type))

def delete_metadata(filename):
    logger.info(f"Deleting metadata for file: {filename}")
    query = """
        DELETE FROM images WHERE filename = %s
    """
    log_success = f"Metadata deleted successfully for {filename}"
    log_fail = "Failed to delete metadata"
    execute_query(query, log_success, log_fail, (filename,))

def get_images_metadata(page=1, page_size=10) -> list:
    logger.debug(f"Fetching images metadata - page: {page}, page_size: {page_size}")
    offset = (page - 1) * page_size
    limit = page_size
    query = """
        SELECT * FROM images 
        ORDER BY upload_time DESC
        LIMIT %s OFFSET %s;
    """
    return fetch_query(query, (limit, offset))

def get_images_count() -> int:
    logger.debug("Getting total images count")
    query = """
        SELECT COUNT(*) FROM images;
    """
    result = fetch_query(query)
    count = result[0][0] if result else 0
    logger.debug(f"Total images count: {count}")
    return count

def get_image_metadata(filename) -> list:
    logger.debug(f"Getting metadata for image: {filename}")
    query = """
        SELECT * FROM images WHERE filename = %s
    """
    result = fetch_query(query, (filename,))
    if not result:
        logger.warning(f"Image not found in database: {filename}")
        raise Exception("Image not found")
    logger.debug(f"Found metadata for {filename}")
    return result[0]