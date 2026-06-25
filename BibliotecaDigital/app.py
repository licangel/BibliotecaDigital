from flask import Flask
from dotenv import load_dotenv
import os

# Cargar variables de entorno
load_dotenv()

# Importar módulos de la aplicación
from config import Config
from database import init_db
from routes import register_routes
from utils import ensure_directories

def create_app():
    """Factory function para crear la aplicación Flask"""
    app = Flask(__name__)
    
    # Configurar la aplicación
    app.config.from_object(Config)
    
    # Crear directorios necesarios
    ensure_directories(app)
    
    # Registrar rutas
    register_routes(app)
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)