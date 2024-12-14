import os
import psycopg2
from psycopg2.extras import RealDictCursor
from flask import Flask, render_template, request,redirect

app = Flask(__name__)

import os

DATABASE_URL = os.environ.get("DATABASE_URL")

# Configuración de la carpeta QR
QR_FOLDER = os.path.join(app.root_path, 'static', 'qr_codes')  # Ruta absoluta del sistema
os.makedirs(QR_FOLDER, exist_ok=True)  # Crea la carpeta si no existe

# Configuración de la base de datos
DATABASE = os.path.join(app.root_path, 'database.db')

def get_db_connection():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

# Inicializar la base de datos
def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pacientes (
            id SERIAL PRIMARY KEY,
            nombre TEXT NOT NULL,
            edad INTEGER NOT NULL,
            diagnostico TEXT,
            qr_path TEXT
        )
    ''')
    conn.commit()
    conn.close()


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate_qr():
    nombre = request.form['nombre']
    edad = request.form['edad']
    diagnostico = request.form['diagnostico']

    # Guardar en la base de datos y obtener el ID
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO pacientes (nombre, edad, diagnostico, qr_path) VALUES (%s, %s, %s, %s) RETURNING id',
                   (nombre, edad, diagnostico, None))
    paciente_id = cursor.fetchone()['id']
    conn.commit()
    conn.close()

    # Generar el código QR
    qr_url = f"https://miapp-flask.onrender.com/paciente/{paciente_id}"
    qr_filename = f"{paciente_id}_{nombre}.png"
    qr_path_full = os.path.join(app.root_path, 'static', 'qr_codes', qr_filename)
    qr_path = f"/static/qr_codes/{qr_filename}"

    import qrcode
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(qr_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    # Guardar el QR
    img.save(qr_path_full)

    # Actualizar la ruta del QR en la base de datos
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE pacientes SET qr_path = %s WHERE id = %s', (qr_path, paciente_id))
    conn.commit()
    conn.close()

    # Renderizar la página con el QR generado
    return render_template('qr.html', nombre=nombre, qr_path=qr_path)


@app.route('/paciente/<int:id>')
def paciente(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT nombre, edad, diagnostico FROM pacientes WHERE id = %s', (id,))
    paciente = cursor.fetchone()
    conn.close()

    if not paciente:
        return "Paciente no encontrado", 404

    return render_template('paciente.html', id=id, nombre=paciente['nombre'], edad=paciente['edad'], diagnostico=paciente['diagnostico'])

@app.route('/pregunta/<int:id>', methods=['POST'])
def guardar_pregunta(id):
    pregunta = request.form['pregunta']

    # Establecer conexión a PostgreSQL
    conn = get_db_connection()
    cursor = conn.cursor()

    # Inserción en la tabla preguntas
    cursor.execute('INSERT INTO preguntas (paciente_id, pregunta) VALUES (%s, %s)', (id, pregunta))
    conn.commit()
    conn.close()

    # Redirigir al paciente
    return redirect(f"/paciente/{id}")



if __name__ == '__main__':
    init_db()  # Inicializar la base de datos al iniciar el servidor
    app.run(debug=True)
