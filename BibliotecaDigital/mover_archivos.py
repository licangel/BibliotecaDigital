from appP import app, db, Upload  # Importa la app Flask y db desde tu appP.py
import os
import shutil
from datetime import datetime

ORIGEN = '/var/elibrary/upload'
DESTINO = '/var/elibrary/books'

def mover_pdfs():
    archivos = [f for f in os.listdir(ORIGEN) if f.lower().endswith('.pdf')]
    if not archivos:
        print("No hay archivos PDF para mover.")
        return

    for archivo in archivos:
        ruta_origen = os.path.join(ORIGEN, archivo)
        ruta_destino = os.path.join(DESTINO, archivo)
        try:
            shutil.move(ruta_origen, ruta_destino)
            print(f"Archivo movido: {archivo}")

            # Registrar en la BD dentro del contexto
            nuevo_upload = Upload(
                user_id=None,
                file_name=archivo,
                file_path=ruta_destino,
                upload_date=datetime.now(),
                processed=True,
                processed_date=datetime.now(),
                book_id=None,
                error_message=None
            )
            db.session.add(nuevo_upload)
            db.session.commit()

        except Exception as e:
            print(f"Error al mover {archivo}: {e}")
            nuevo_upload = Upload(
                user_id=None,
                file_name=archivo,
                file_path=ruta_origen,
                upload_date=datetime.now(),
                processed=False,
                processed_date=datetime.now(),
                book_id=None,
                error_message=str(e)
            )
            db.session.add(nuevo_upload)
            db.session.commit()

if __name__ == "__main__":
    with app.app_context():
        mover_pdfs()
