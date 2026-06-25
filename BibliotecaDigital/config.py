import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Configuraciones de la aplicación"""
    SECRET_KEY = os.getenv('SECRET_KEY', 'tu_clave_secreta_aqui')
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', '/var/elibrary/upload')
    BOOKS_FOLDER = os.getenv('BOOKS_FOLDER', '/var/elibrary/books')
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))
    
    # Configuración de base de datos
    DB_CONFIG = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'database': os.getenv('DB_NAME', 'biblioteca_db'),
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD', 'postgres'),
        'port': int(os.getenv('DB_PORT', 5432)),
    }