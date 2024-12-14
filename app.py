from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import os

# Cargar variables de entorno
load_dotenv()

app = Flask(_name_)

# Configuración de la base de datos
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')  # Asegúrate de que DATABASE_URL esté configurado correctamente
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicializar la base de datos
db = SQLAlchemy(app)

# Modelo para almacenar datos QR
class QRModel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    qr_content = db.Column(db.Text, nullable=False)

def init_db():
    with app.app_context():
        db.create_all()

@app.route('/save_qr', methods=['POST'])
def save_qr():
    try:
        data = request.json
        if not data or 'qr_data' not in data:
            return jsonify({"error": "Faltan datos de entrada"}), 400

        qr_data = data['qr_data']
        new_qr = QRModel(qr_content=qr_data)
        db.session.add(new_qr)
        db.session.commit()

        return jsonify({"message": "QR guardado correctamente", "id": new_qr.id}), 201

    except Exception as e:
        return jsonify({"error": f"Error al guardar QR: {str(e)}"}), 500

@app.route('/get_qr/<int:qr_id>', methods=['GET'])
def get_qr(qr_id):
    try:
        qr_entry = QRModel.query.get(qr_id)
        if not qr_entry:
            return jsonify({"error": "QR no encontrado"}), 404

        return jsonify({"id": qr_entry.id, "qr_content": qr_entry.qr_content}), 200

    except Exception as e:
        return jsonify({"error": f"Error al recuperar QR: {str(e)}"}), 500

@app.route('/list_qrs', methods=['GET'])
def list_qrs():
    try:
        qrs = QRModel.query.all()
        qr_list = [{"id": qr.id, "qr_content": qr.qr_content} for qr in qrs]

        return jsonify(qr_list), 200

    except Exception as e:
        return jsonify({"error": f"Error al listar QRs: {str(e)}"}), 500

if _name_ == '_main_':
    init_db()
    app.run(debug=True)
