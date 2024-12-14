import os
import sqlite3  # Biblioteca para trabajar con SQLite
from flask import Flask, render_template, request

app = Flask(__name__)

# Configuración de la carpeta QR
QR_FOLDER = os.path.join(app.root_path, 'static', 'qr_codes')  # Ruta absoluta del sistema
os.makedirs(QR_FOLDER, exist_ok=True)  # Crea la carpeta si no existe

# Configuración de la base de datos
DATABASE = os.path.join(app.root_path, 'database.db')

# Inicializar la base de datos
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


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate_qr():
    nombre = request.form['nombre']
    edad = request.form['edad']
    diagnostico = request.form['diagnostico']

    # Guardar en la base de datos para obtener el ID
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO pacientes (nombre, edad, diagnostico, qr_path) VALUES (?, ?, ?, ?)',
                   (nombre, edad, diagnostico, None))
    paciente_id = cursor.lastrowid  # Obtener el ID del paciente recién insertado
    conn.commit()
    conn.close()

    # Generar URL del QR con el ID del paciente
    qr_url = f"http://127.0.0.1:5000/paciente/{paciente_id}"
    qr_filename = f"{nombre}_{edad}.png"
    qr_path_full = os.path.join(QR_FOLDER, qr_filename)
    qr_path = f"/static/qr_codes/{qr_filename}"

    # Crear el QR
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

    # Actualizar la base de datos con la ruta del QR
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('UPDATE pacientes SET qr_path = ? WHERE id = ?', (qr_path, paciente_id))
    conn.commit()
    conn.close()

    # Renderizar la página del QR
    return render_template('qr.html', nombre=nombre, qr_path=qr_path)

@app.route('/paciente/<int:id>')
def paciente(id):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('SELECT nombre, edad, diagnostico FROM pacientes WHERE id = ?', (id,))
    paciente = cursor.fetchone()
    conn.close()

    if not paciente:
        return "Paciente no encontrado", 404

    return render_template('paciente.html', id=id, nombre=paciente[0], edad=paciente[1], diagnostico=paciente[2])

@app.route('/pregunta/<int:id>', methods=['POST'])
def guardar_pregunta(id):
    pregunta = request.form['pregunta']

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO preguntas (paciente_id, pregunta) VALUES (?, ?)', (id, pregunta))
    conn.commit()
    conn.close()

    return redirect(f"/paciente/{id}")


if __name__ == '__main__':
    init_db()  # Inicializar la base de datos al iniciar el servidor
    app.run(debug=True)
