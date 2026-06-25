import os
from config import Config

def ensure_directories(app=None):
    """Crear directorios necesarios si no existen"""
    directories = [
        Config.UPLOAD_FOLDER,
        Config.BOOKS_FOLDER
    ]
    
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory, mode=0o755)
            print(f"Directorio creado: {directory}")