import os
import firebase_admin
from firebase_admin import credentials, firestore
from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv
import cv2
import base64
import time

load_dotenv()

app = Flask(__name__)

# ------------------ Inicializar Firebase Admin SDK ------------------
firebase_key_path = None

# 1. Priorizar archivo local (más cómodo para desarrollo)
local_key = "serviceAccountKey.json"
if os.path.exists(local_key):
    firebase_key_path = local_key
    print("✅ Usando credenciales locales: serviceAccountKey.json")
else:
    # 2. Intentar variable GOOGLE_APPLICATION_CREDENTIALS
    firebase_key_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if not firebase_key_path:
        # 3. Intentar variable FIRESTORE_KEY_PATH
        firebase_key_path = os.getenv("FIRESTORE_KEY_PATH")
    if firebase_key_path and os.path.exists(firebase_key_path):
        print(f"✅ Usando credenciales desde variable: {firebase_key_path}")
    else:
        firebase_key_path = None

if not firebase_key_path:
    raise Exception("No se encontraron credenciales de Firebase. Coloca serviceAccountKey.json en la carpeta del proyecto o define GOOGLE_APPLICATION_CREDENTIALS/FIRESTORE_KEY_PATH")

cred = credentials.Certificate(firebase_key_path)
firebase_admin.initialize_app(cred)
db = firestore.client()

# ------------------ Ruta principal ------------------
@app.route('/')
def index():
    return render_template('index.html')

# ------------------ API validación de código (RF-03) ------------------
@app.route('/validate', methods=['POST'])
def validate_code():
    data = request.get_json()
    codigo = data.get('codigo', '').strip().upper()

    if not codigo or len(codigo) != 4:
        return jsonify({"valido": False, "error": "Código inválido"}), 400

    try:
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

# ------------------ Cámara y captura (RF-04) ------------------
camera = None

def init_camera():
    global camera
    camera_index = int(os.getenv('CAMERA_INDEX', 0))
    try:
        camera = cv2.VideoCapture(camera_index)
        if not camera.isOpened():
            print(f"⚠️ Advertencia: No se pudo abrir la cámara índice {camera_index}")
            camera = None
        else:
            print(f"✅ Cámara inicializada correctamente (índice {camera_index})")
    except Exception as e:
        print(f"❌ Error al inicializar cámara: {e}")
        camera = None

@app.route('/capturar', methods=['POST'])
def capturar():
    global camera
    if camera is None:
        init_camera()
        if camera is None:
            return jsonify({"error": "Cámara no disponible"}), 500

    success = False
    frame = None
    start_time = time.time()
    while time.time() - start_time < 3:
        ret, frame = camera.read()
        if ret:
            success = True
            break
        time.sleep(0.1)

    if not success or frame is None:
        return jsonify({"error": "No se pudo capturar imagen (timeout o cámara sin respuesta)"}), 500

    # Redimensionar a 224x224
    resized = cv2.resize(frame, (224, 224))

    # Codificar a JPEG en base64
    _, buffer = cv2.imencode('.jpg', resized)
    img_base64 = base64.b64encode(buffer).decode('utf-8')

    return jsonify({
        "success": True,
        "image": img_base64,
        "width": 224,
        "height": 224
    })

# ------------------ Inicio del servidor ------------------
if __name__ == '__main__':
    init_camera()
    port = int(os.getenv('FLASK_PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)