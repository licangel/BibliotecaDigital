import psycopg2
import psycopg2.extras
from config import Config

def get_db_connection():
    """Crear conexión a la base de datos"""
    try:
        conn = psycopg2.connect(**Config.DB_CONFIG)
        return conn
    except psycopg2.Error as e:
        print(f"Error conectando a la base de datos: {e}")
        return None

def init_db():
    """Inicializar la base de datos si es necesario"""
    # Aquí puedes agregar código para crear tablas si no existen
    pass

class BookRepository:
    """Repositorio para operaciones de libros"""
    
    @staticmethod
    def get_all_books():
        """Obtener todos los libros disponibles"""
        conn = get_db_connection()
        books = []
        
        if conn:
            try:
                cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
                cursor.execute("""
                    SELECT b.id, b.isbn, b.title, b.publication_year, b.description, 
                           b.upload_date, b.download_count, b.available,
                           a.name as author_name, p.name as publisher_name,
                           u.username as uploaded_by_username
                    FROM books b
                    LEFT JOIN authors a ON b.author_id = a.id
                    LEFT JOIN publishers p ON b.publisher_id = p.id
                    LEFT JOIN users u ON b.uploaded_by = u.id
                    WHERE b.available = TRUE
                    ORDER BY b.upload_date DESC
                """)
                books = cursor.fetchall()
            except psycopg2.Error as e:
                print(f'Error cargando libros: {e}')
            finally:
                conn.close()
        
        return books
    
    @staticmethod
    def get_book_by_id(book_id):
        """Obtener libro por ID"""
        conn = get_db_connection()
        book = None
        
        if conn:
            try:
                cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
                cursor.execute("SELECT file_path, title FROM books WHERE id = %s AND available = TRUE", (book_id,))
                book = cursor.fetchone()
            except psycopg2.Error as e:
                print(f'Error obteniendo libro: {e}')
            finally:
                conn.close()
        
        return book
    
    @staticmethod
    def increment_download_count(book_id):
        """Incrementar contador de descargas"""
        conn = get_db_connection()
        
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("UPDATE books SET download_count = download_count + 1 WHERE id = %s", (book_id,))
                conn.commit()
            except psycopg2.Error as e:
                print(f'Error actualizando contador: {e}')
            finally:
                conn.close()

class UserRepository:
    """Repositorio para operaciones de usuarios"""
    
    @staticmethod
    def get_user_by_username(username):
        """Obtener usuario por nombre de usuario"""
        conn = get_db_connection()
        user = None
        
        if conn:
            try:
                cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
                cursor.execute("SELECT id, username, password_hash FROM users WHERE username = %s", (username,))
                user = cursor.fetchone()
            except psycopg2.Error as e:
                print(f'Error obteniendo usuario: {e}')
            finally:
                conn.close()
        
        return user
    
    @staticmethod
    def create_user(username, email, password_hash):
        """Crear nuevo usuario"""
        from datetime import datetime
        conn = get_db_connection()
        success = False
        
        if conn:
            try:
                cursor = conn.cursor()
                
                # Verificar si el usuario ya existe
                cursor.execute("SELECT id FROM users WHERE username = %s OR email = %s", (username, email))
                if cursor.fetchone():
                    return False, "El usuario o email ya existe"
                
                # Crear nuevo usuario
                cursor.execute("""
                    INSERT INTO users (username, email, password_hash, created_at) 
                    VALUES (%s, %s, %s, %s)
                """, (username, email, password_hash, datetime.now()))
                
                conn.commit()
                success = True
                
            except psycopg2.Error as e:
                print(f'Error creando usuario: {e}')
                return False, f"Error registrando usuario: {e}"
            finally:
                conn.close()
        
        return success, "Usuario registrado exitosamente" if success else "Error de conexión"