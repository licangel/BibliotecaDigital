from flask import render_template, request, redirect, url_for, flash, session, send_file
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
from datetime import datetime
import uuid

from database import BookRepository, UserRepository
from book_service import BookService

def register_routes(app):
    """Registrar todas las rutas de la aplicación"""
    
    @app.route('/')
    def index():
        """Página principal - redirige al login si no está autenticado"""
        if 'user_id' in session:
            return redirect(url_for('repository'))
        return redirect(url_for('login'))

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        """Página de inicio de sesión"""
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            
            if not username or not password:
                flash('Por favor complete todos los campos', 'error')
                return render_template('login.html')
            
            user = UserRepository.get_user_by_username(username)
            
            if user and check_password_hash(user['password_hash'], password):
                session['user_id'] = user['id']
                session['username'] = user['username']
                flash('Inicio de sesión exitoso', 'success')
                return redirect(url_for('repository'))
            else:
                flash('Credenciales inválidas', 'error')
        
        return render_template('login.html')

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        """Registro de usuarios"""
        if request.method == 'POST':
            username = request.form.get('username')
            email = request.form.get('email')
            password = request.form.get('password')
            
            if not username or not email or not password:
                flash('Por favor complete todos los campos', 'error')
                return render_template('register.html')
            
            password_hash = generate_password_hash(password)
            success, message = UserRepository.create_user(username, email, password_hash)
            
            if success:
                flash(message, 'success')
                return redirect(url_for('login'))
            else:
                flash(message, 'error')
        
        return render_template('register.html')

    @app.route('/logout')
    def logout():
        """Cerrar sesión"""
        session.clear()
        flash('Sesión cerrada', 'info')
        return redirect(url_for('login'))

    @app.route('/repository')
    def repository():
        """Página del repositorio de libros"""
        if 'user_id' not in session:
            return redirect(url_for('login'))
        
        books = BookRepository.get_all_books()
        return render_template('repository.html', books=books)

    @app.route('/upload', methods=['GET', 'POST'])
    def upload():
        """Página de subida de libros"""
        if 'user_id' not in session:
            return redirect(url_for('login'))
        
        if request.method == 'POST':
            # Verificar si se subió un archivo
            if 'file' not in request.files:
                flash('No se seleccionó archivo', 'error')
                return redirect(request.url)
            
            file = request.files['file']
            
            if file.filename == '':
                flash('No se seleccionó archivo', 'error')
                return redirect(request.url)
            
            if file and file.filename.lower().endswith('.pdf'):
                try:
                    # Procesar el archivo usando BookService
                    success, message = BookService.process_uploaded_book(file, session['user_id'])
                    
                    if success:
                        flash(message, 'success')
                    else:
                        flash(message, 'error')
                        
                except Exception as e:
                    flash(f'Error subiendo archivo: {e}', 'error')
            else:
                flash('Solo se permiten archivos PDF', 'error')
            
            return redirect(url_for('upload'))
        
        return render_template('upload.html')

    @app.route('/download/<int:book_id>')
    def download_book(book_id):
        """Descargar libro"""
        if 'user_id' not in session:
            return redirect(url_for('login'))
        
        book = BookRepository.get_book_by_id(book_id)
        
        if book and os.path.exists(book['file_path']):
            # Incrementar contador de descargas
            BookRepository.increment_download_count(book_id)
            
            # Servir el archivo
            return send_file(book['file_path'], as_attachment=True, download_name=f"{book['title']}.pdf")
        else:
            flash('Libro no encontrado o archivo no disponible', 'error')
        
        return redirect(url_for('repository'))

    @app.route('/read/<int:book_id>')
    def read_book(book_id):
        """Leer libro online (PDF viewer)"""
        if 'user_id' not in session:
            return redirect(url_for('login'))
        
        book = BookRepository.get_book_by_id(book_id)
        
        if book and os.path.exists(book['file_path']):
            # Servir el archivo para lectura online
            return send_file(book['file_path'], mimetype='application/pdf')
        else:
            flash('Libro no encontrado o archivo no disponible', 'error')
        
        return redirect(url_for('repository'))