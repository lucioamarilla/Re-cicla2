import os
import firebase_admin
from firebase_admin import credentials, firestore
from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv
import functools

load_dotenv()

app = Flask(__name__)

# ------------------ Inicializar Firebase Admin SDK ------------------
# Reemplaza estas líneas:
# firebase_key_path = os.getenv("FIRESTORE_KEY_PATH", "serviceAccountKey.json")


firebase_key_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
if not firebase_key_path:
    raise Exception("Variable de entorno GOOGLE_APPLICATION_CREDENTIALS no configurada")
cred = credentials.Certificate(firebase_key_path)
firebase_admin.initialize_app(cred)
db = firestore.client()

# ------------------ Ruta principal ------------------
@app.route('/')
def index():
    return render_template('index.html')

# ------------------ API validación de código ------------------
@app.route('/validate', methods=['POST'])
def validate_code():
    data = request.get_json()
    codigo = data.get('codigo', '').strip().upper()

    if not codigo or len(codigo) != 4:
        return jsonify({"valido": False, "error": "Código inválido"}), 400

    try:
        # Buscar documento en la colección "users" con ID = codigo
        doc_ref = db.collection('users').document(codigo)
        doc = doc_ref.get()
        if doc.exists:
            user_data = doc.to_dict()
            nombre = user_data.get('nombre', codigo)
            return jsonify({"valido": True, "nombre": nombre})
        else:
            return jsonify({"valido": False, "nombre": None})
    except Exception as e:
        print(f"Error en Firestore: {e}")
        return jsonify({"valido": False, "error": "Error interno"}), 500

# ------------------ Inicio del servidor ------------------
if __name__ == '__main__':
    port = int(os.getenv('FLASK_PORT', 5000))
    # host='0.0.0.0' permite acceso desde otros dispositivos en la red local (opcional)
    app.run(host='0.0.0.0', port=port, debug=True)