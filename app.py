# Configuración de la carpeta QR
import os
import sqlite3  # Biblioteca para trabajar con SQLite
from flask import Flask, render_template, request

app = Flask(__name__)

QR_FOLDER = os.path.join(app.root_path, 'static', 'qr_codes')  # Ruta absoluta del sistema
os.makedirs(QR_FOLDER, exist_ok=True)  # Crea la carpeta si no existe

# Configuración de la base de datos
DATABASE = os.path.join(app.root_path, 'database.db')

@app.route('/')
def index():
    return render_template('index.html')

def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pacientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT,
            edad INTEGER,
            diagnostico TEXT,
            qr_path TEXT
        )
    ''')
    conn.commit()
    conn.close()

@app.route('/generate', methods=['POST'])
def generate_qr():
    nombre = request.form['nombre']
    edad = request.form['edad']
    diagnostico = request.form['diagnostico']

    # Ruta para guardar el QR
    qr_filename = f"{nombre}_{edad}.png"
    qr_path_full = os.path.join(QR_FOLDER, qr_filename)  # Ruta absoluta en el sistema
    qr_path = f"/static/qr_codes/{qr_filename}"  # Ruta accesible desde el navegador

    # Guardar los datos en la base de datos
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO pacientes (nombre, edad, diagnostico, qr_path) VALUES (?, ?, ?, ?)',
                   (nombre, edad, diagnostico, qr_path))
    conn.commit()
    conn.close()

    # Crear el QR
    import qrcode
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(f"http://example.com/{nombre}")
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    # Guardar la imagen
    img.save(qr_path_full)

    # Redirigir a la página qr.html con los datos
    return render_template('qr.html', nombre=nombre, qr_path=qr_path)

if __name__ == '__main__':
    app.run(debug=True)
