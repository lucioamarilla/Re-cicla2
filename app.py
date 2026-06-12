import os
import base64
import time
import json
import requests
import firebase_admin
from firebase_admin import credentials, firestore
from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv
import cv2

load_dotenv()

app = Flask(__name__)

# ------------------ Inicializar Firebase Admin SDK ------------------
firebase_key_path = None
local_key = "serviceAccountKey.json"
if os.path.exists(local_key):
    firebase_key_path = local_key
    print("✅ Usando credenciales locales: serviceAccountKey.json")
else:
    firebase_key_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if not firebase_key_path:
        firebase_key_path = os.getenv("FIRESTORE_KEY_PATH")
    if firebase_key_path and os.path.exists(firebase_key_path):
        print(f"✅ Usando credenciales desde variable: {firebase_key_path}")
    else:
        firebase_key_path = None

if firebase_key_path:
    cred = credentials.Certificate(firebase_key_path)
    firebase_admin.initialize_app(cred)
    db = firestore.client()
    print("✅ Firebase inicializado correctamente")
else:
    db = None
    print("⚠️ Firebase no configurado: las transacciones no se guardarán")

# ------------------ Configuración Roboflow ------------------
ROBOFLOW_API_KEY = os.getenv("ROBOFLOW_API_KEY")
ROBOFLOW_MODEL_ID = os.getenv("ROBOFLOW_MODEL_ID")
ROBOFLOW_VERSION = os.getenv("ROBOFLOW_VERSION")
ROBOFLOW_TIMEOUT = int(os.getenv("ROBOFLOW_TIMEOUT", 10))
CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", 0.70))

# Mapeo de clases de Roboflow a etiquetas internas
MAPEO_CLASES = {
    "plastic": "plastico",
    "cardboard": "carton",
    "trash": "rechazo"
}

# ------------------ Inicializar cámara ------------------
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

# ------------------ Funciones auxiliares ------------------
def clasificar_con_roboflow(imagen_base64):
    """Envía imagen a Roboflow y retorna (material, confidence) o lanza excepción"""
    url = f"https://detect.roboflow.com/{ROBOFLOW_MODEL_ID}/{ROBOFLOW_VERSION}?api_key={ROBOFLOW_API_KEY}"
    payload = {"base64_image": imagen_base64}
    try:
        response = requests.post(url, data=payload, timeout=ROBOFLOW_TIMEOUT)
        response.raise_for_status()
        data = response.json()
        predictions = data.get("predictions", [])
        if not predictions:
            return "rechazo", 0.0
        # Tomar la predicción con mayor confidence
        best = max(predictions, key=lambda x: x.get("confidence", 0))
        clase_raw = best.get("class", "").lower()
        confidence = best.get("confidence", 0.0)
        material = MAPEO_CLASES.get(clase_raw, "rechazo")
        return material, confidence
    except requests.exceptions.Timeout:
        raise Exception("timeout")
    except requests.exceptions.RequestException as e:
        raise Exception(f"error_api: {str(e)}")

def evaluar_puntos(material, confidence):
    """Retorna 1 si cumple reglas, 0 en caso contrario"""
    if material in ["plastico", "carton"] and confidence >= CONFIDENCE_THRESHOLD:
        return 1
    return 0

def registrar_transaccion(user_id, nombre, material, puntos, confidence):
    """Guarda transacción y actualiza saldo atómicamente en Firestore"""
    if db is None:
        print("Firestore no disponible, transacción no guardada")
        return False
    try:
        # Usar transacción de Firestore para atomicidad
        transaction = db.transaction()
        user_ref = db.collection('users').document(user_id)

        def update_callback(transaction):
            doc = transaction.get(user_ref)
            if not doc.exists:
                # Si no existe, lo creamos con saldo inicial 0
                transaction.set(user_ref, {"nombre": nombre, "saldo": 0})
                saldo_actual = 0
            else:
                saldo_actual = doc.get("saldo") or 0
            nuevo_saldo = saldo_actual + puntos
            transaction.update(user_ref, {"saldo": nuevo_saldo})
            return nuevo_saldo

        nuevo_saldo = transaction.run(update_callback)

        # Crear documento de transacción
        transaccion_ref = db.collection('transactions').document()
        transaccion_ref.set({
            "userId": user_id,
            "nombre": nombre,
            "material": material,
            "puntos": puntos,
            "confidence": confidence,
            "timestamp": firestore.SERVER_TIMESTAMP
        })
        print(f"✅ Transacción registrada: {user_id} +{puntos} puntos (nuevo saldo: {nuevo_saldo})")
        return True
    except Exception as e:
        print(f"❌ Error al registrar transacción: {e}")
        return False

# ------------------ Rutas Flask ------------------
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/validate', methods=['POST'])
def validate_code():
    data = request.get_json()
    codigo = data.get('codigo', '').strip().upper()
    if not codigo or len(codigo) != 4:
        return jsonify({"valido": False, "error": "Código inválido"}), 400
    if db is None:
        # Modo debug sin Firebase: aceptamos cualquier código
        return jsonify({"valido": True, "nombre": f"Usuario {codigo}"})
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
        return jsonify({"error": "No se pudo capturar imagen (timeout)"}), 500
    # Redimensionar a 224x224
    resized = cv2.resize(frame, (224, 224))
    _, buffer = cv2.imencode('.jpg', resized)
    img_base64 = base64.b64encode(buffer).decode('utf-8')
    return jsonify({
        "success": True,
        "image": img_base64,
        "width": 224,
        "height": 224
    })

@app.route('/clasificar', methods=['POST'])
def clasificar():
    data = request.get_json()
    imagen_base64 = data.get('imagen_base64')
    user_id = data.get('user_id')
    nombre_usuario = data.get('nombre')
    if not imagen_base64 or not user_id or not nombre_usuario:
        return jsonify({"error": "Faltan datos (imagen_base64, user_id, nombre)"}), 400

    try:
        # RF-05: Clasificación
        material, confidence = clasificar_con_roboflow(imagen_base64)
        # RF-06: Puntos
        puntos = evaluar_puntos(material, confidence)
        # RF-07: Transacción
        ok = registrar_transaccion(user_id, nombre_usuario, material, puntos, confidence)
        if not ok:
            return jsonify({
                "success": True,
                "material": material,
                "confidence": confidence,
                "puntos": puntos,
                "warning": "Transacción no guardada (Firestore no disponible)"
            })
        return jsonify({
            "success": True,
            "material": material,
            "confidence": confidence,
            "puntos": puntos
        })
    except Exception as e:
        mensaje = str(e)
        if mensaje == "timeout":
            return jsonify({"error": "timeout"}), 504
        if mensaje.startswith("error_api"):
            return jsonify({"error": "error_api", "detalle": mensaje}), 502
        return jsonify({"error": "clasificacion_fallida", "detalle": mensaje}), 500

# ------------------ Inicio del servidor ------------------
if __name__ == '__main__':
    init_camera()
    port = int(os.getenv('FLASK_PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)