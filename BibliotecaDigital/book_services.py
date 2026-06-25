import os
import uuid
import shutil
import requests
import PyPDF2
import re
import psycopg2
from datetime import datetime
from werkzeug.utils import secure_filename

from config import Config
from database import get_db_connection

class BookService:
    """Servicio para manejo de libros"""
    
    @staticmethod
    def extract_isbn_from_pdf(filepath):
        """Extraer ISBN del PDF"""
        try:
            with open(filepath, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    text = page.extract_text()
                    if text:
                        # Buscar patrones de ISBN 13 (empiezan con 978 o 979)
                        matches = re.findall(r'97[89][- ]?\d{1,5}[- ]?\d{1,7}[- ]?\d{1,7}[- ]?\d', text)
                        if matches:
                            # Devuelve el primer ISBN encontrado, limpiando guiones y espacios
                            return matches[0].replace('-', '').replace(' ', '')
        except Exception as e:
            print(f"Error al extraer ISBN: {e}")
        return None
    
    @staticmethod
    def get_book_info_from_isbn(isbn):
        """Obtener información del libro desde OpenLibrary API"""
        try:
            isbn_clean = isbn.replace('-', '').replace(' ', '')
            url = f"https://openlibrary.org/api/books?bibkeys=ISBN:{isbn_clean}&format=json&jscmd=data"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                book_key = f"ISBN:{isbn_clean}"
                if book_key in data:
                    book_data = data[book_key]
                    return {
                        'title': book_data.get('title', ''),
                        'authors': [author['name'] for author in book_data.get('authors', [])],
                        'publishers': [pub['name'] for pub in book_data.get('publishers', [])],
                        'publish_date': book_data.get('publish_date', ''),
                        'description': book_data.get('description', {}).get('value', '') if isinstance(book_data.get('description'), dict) else book_data.get('description', ''),
                        'subjects': book_data.get('subjects', [])
                    }
        except Exception as e:
            print(f"Error obteniendo datos de OpenLibrary: {e}")
        return None
    
    @staticmethod
    def move_file_to_books(upload_path, filename):
        """Mover archivo de upload a books folder"""
        try:
            books_path = os.path.join(Config.BOOKS_FOLDER, filename)
            shutil.move(upload_path, books_path)
            return books_path
        except Exception as e:
            print(f"Error moviendo archivo: {e}")
            return None
    
    @staticmethod
    def create_or_get_author(cursor, author_name):
        """Crear o obtener autor"""
        if not author_name:
            return None
            
        cursor.execute("SELECT id FROM authors WHERE name = %s", (author_name,))
        author = cursor.fetchone()
        if author:
            return author[0]
        else:
            cursor.execute("INSERT INTO authors (name) VALUES (%s) RETURNING id", (author_name,))
            return cursor.fetchone()[0]
    
    @staticmethod
    def create_or_get_publisher(cursor, publisher_name):
        """Crear o obtener publisher"""
        if not publisher_name:
            return None
            
        cursor.execute("SELECT id FROM publishers WHERE name = %s", (publisher_name,))
        publisher = cursor.fetchone()
        if publisher:
            return publisher[0]
        else:
            cursor.execute("INSERT INTO publishers (name) VALUES (%s) RETURNING id", (publisher_name,))
            return cursor.fetchone()[0]
    
    @staticmethod
    def extract_publication_year(publish_date):
        """Extraer año de publicación"""
        if not publish_date:
            return None
        try:
            return int(publish_date.split()[-1])
        except:
            return None
    
    @staticmethod
    def process_uploaded_book(file, user_id):
        """Procesar archivo de libro subido"""
        from utils import ensure_directories
        
        # Crear directorios si no existen
        ensure_directories(None)
        
        # Generar nombre único para el archivo
        filename = secure_filename(f"{uuid.uuid4()}_{file.filename}")
        upload_path = os.path.join(Config.UPLOAD_FOLDER, filename)
        
        try:
            # Guardar archivo temporalmente en upload
            file.save(upload_path)
            
            # Extraer ISBN desde el PDF subido
            isbn = BookService.extract_isbn_from_pdf(upload_path)
            if not isbn:
                if os.path.exists(upload_path):
                    os.remove(upload_path)
                return False, 'No se pudo extraer un ISBN válido del archivo PDF.'

            # Obtener información del libro usando ISBN extraído
            book_info = BookService.get_book_info_from_isbn(isbn)
            if not book_info:
                if os.path.exists(upload_path):
                    os.remove(upload_path)
                return False, f'No se encontró información para el ISBN {isbn} en OpenLibrary.'
            
            conn = get_db_connection()
            if not conn:
                if os.path.exists(upload_path):
                    os.remove(upload_path)
                return False, 'Error de conexión a la base de datos'
            
            try:
                cursor = conn.cursor()
                
                # Registrar en tabla uploads
                cursor.execute("""
                    INSERT INTO uploads (user_id, file_name, file_path, upload_date, processed)
                    VALUES (%s, %s, %s, %s, %s) RETURNING id
                """, (user_id, file.filename, upload_path, datetime.now(), False))
                
                upload_id = cursor.fetchone()[0]
                
                # Mover archivo a books folder
                final_path = BookService.move_file_to_books(upload_path, filename)
                
                if not final_path:
                    return False, 'Error moviendo archivo a biblioteca'
                
                # Crear/obtener autor y publisher
                author_id = None
                if book_info.get('authors'):
                    author_id = BookService.create_or_get_author(cursor, book_info['authors'][0])
                
                publisher_id = None
                if book_info.get('publishers'):
                    publisher_id = BookService.create_or_get_publisher(cursor, book_info['publishers'][0])
                
                # Extraer año de publicación
                publication_year = BookService.extract_publication_year(book_info.get('publish_date'))
                
                # Crear libro con la ruta final
                cursor.execute("""
                    INSERT INTO books (isbn, title, author_id, publisher_id, publication_year, 
                                     description, upload_date, uploaded_by, file_path, 
                                     download_count, available)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
                """, (isbn, book_info.get('title', 'Título no encontrado'), author_id, publisher_id,
                      publication_year, book_info.get('description', ''), datetime.now(),
                      user_id, final_path, 0, True))
                
                book_id = cursor.fetchone()[0]
                
                # Actualizar upload como procesado
                cursor.execute("""
                    UPDATE uploads SET processed = TRUE, processed_date = %s, book_id = %s
                    WHERE id = %s
                """, (datetime.now(), book_id, upload_id))
                
                conn.commit()
                return True, 'Libro subido y procesado exitosamente'
                
            except psycopg2.Error as e:
                # Limpiar archivo temporal si hay error
                if os.path.exists(upload_path):
                    os.remove(upload_path)
                return False, f'Error procesando archivo: {e}'
            finally:
                conn.close()
                
        except Exception as e:
            if os.path.exists(upload_path):
                os.remove(upload_path)
            return False, f'Error subiendo archivo: {e}'