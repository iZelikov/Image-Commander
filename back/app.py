from flask import Flask, request, jsonify, send_file
import os
import logging
from logging.handlers import RotatingFileHandler
from werkzeug.utils import secure_filename
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime

app = Flask(__name__)

# Конфигурация
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/postgres')
UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', '../images')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 16MB max file size

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# Настройка логирования
if not os.path.exists('../logs'):
    os.makedirs('../logs')

log_handler = RotatingFileHandler(
    '../logs/app.log',
    maxBytes=10485760,  # 10MB
    backupCount=5
)
log_handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
))
app.logger.addHandler(log_handler)
app.logger.setLevel(logging.INFO)


def get_db_connection():
    conn = psycopg2.connect(DATABASE_URL)
    return conn


def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def index():
    return jsonify({"title": 'Image Commander API', "version": "0.1"})

@app.route('/health')
def health():
    app.logger.info('Health check requested')
    return jsonify({'status': 'ok', 'timestamp': datetime.now().isoformat()})


@app.route('/upload', methods=['POST'])
def upload_image():
    app.logger.info('Image upload requested')

    if 'file' not in request.files:
        app.logger.warning('No file part in upload request')
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']

    if file.filename == '':
        app.logger.warning('Empty filename in upload request')
        return jsonify({'error': 'No selected file'}), 400

    if file and allowed_file(file.filename):
        # Безопасное имя файла
        filename = secure_filename(file.filename)

        # Добавляем timestamp для уникальности
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}_{filename}"

        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        app.logger.info(f'Image uploaded successfully: {filename}')

        # Сохраняем информацию в БД (пример)
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute(
                'INSERT INTO images (filename, path, uploaded_at) VALUES (%s, %s, %s)',
                (filename, f'/images/{filename}', datetime.now())
            )
            conn.commit()
            cur.close()
            conn.close()
        except Exception as e:
            app.logger.error(f'Database error: {str(e)}')
            # Продолжаем даже если ошибка БД

        return jsonify({
            'success': True,
            'filename': filename,
            'url': f'/images/{filename}',
            'message': 'File uploaded successfully'
        }), 200
    else:
        app.logger.warning(f'Invalid file type: {file.filename}')
        return jsonify({'error': 'Invalid file type'}), 400


@app.route('/images')
def list_images():
    app.logger.info('Image list requested')
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute('SELECT * FROM images ORDER BY uploaded_at DESC')
        images = cur.fetchall()
        cur.close()
        conn.close()
        return jsonify({'images': images})
    except Exception as e:
        app.logger.error(f'Database error: {str(e)}')
        return jsonify({'error': str(e)}), 500


@app.route('/logs')
def get_logs():
    """Эндпоинт для получения логов (только для разработки)"""
    try:
        with open('../logs/app.log', 'r') as f:
            logs = f.read()
        return jsonify({'logs': logs})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    # Создаём таблицу для изображений если её нет
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('''
            CREATE TABLE IF NOT EXISTS images (
                id SERIAL PRIMARY KEY,
                filename VARCHAR(255) NOT NULL,
                path VARCHAR(500) NOT NULL,
                uploaded_at TIMESTAMP NOT NULL
            )
        ''')
        conn.commit()
        cur.close()
        conn.close()
        app.logger.info('Database table created/verified')
    except Exception as e:
        app.logger.error(f'Database initialization error: {str(e)}')

    app.run(host='0.0.0.0', port=8000, debug=False)