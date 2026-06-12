"""
Re-cicla - Backend PC
----------------------
Servidor Flask que:
  1. Valida el código de 4 dígitos del usuario contra Firestore.
  2. Captura una foto con la webcam (OpenCV).
  3. Envía la imagen a Roboflow para clasificación (plástico/cartón/rechazo).
  4. Acredita puntos en Firestore (colección "usuarios") y registra
     la transacción (colección "transacciones").

Requisitos (instalar con pip):
    pip install flask flask-cors opencv-python requests
    pip install firebase-admin
    pip install python-dotenv

Antes de correr:
  - Colocar el JSON del service account de Firebase como
    "firebase_credentials.json" en esta misma carpeta
    (o ajustar FIREBASE_CREDENTIALS en .env).
  - Verificar que la webcam esté conectada (índice 0 por defecto).

Ejecutar:
    python app.py
"""

import os
import io
import base64
import datetime

import cv2
import requests
from flask import Flask, jsonify, request, render_template, Response
from flask_cors import CORS
from dotenv import load_dotenv

import firebase_admin
from firebase_admin import credentials, firestore

# ---------------------------------------------------------------------------
# Configuración
# ---------------------------------------------------------------------------
load_dotenv()

ROBOFLOW_MODEL = os.getenv("ROBOFLOW_MODEL")
ROBOFLOW_VERSION = os.getenv("ROBOFLOW_VERSION")
ROBOFLOW_API_KEY = os.getenv("ROBOFLOW_API_KEY")
ROBOFLOW_URL = (
    f"https://detect.roboflow.com/{ROBOFLOW_MODEL}/{ROBOFLOW_VERSION}"
    f"?api_key={ROBOFLOW_API_KEY}"
)

FIREBASE_CREDENTIALS = os.getenv("FIREBASE_CREDENTIALS", "firebase_credentials.json")

CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", "0.5"))

PUNTOS_POR_MATERIAL = {
    "plastico": int(os.getenv("PUNTOS_PLASTICO", "1")),
    "carton": int(os.getenv("PUNTOS_CARTON", "1")),
    "rechazo": int(os.getenv("PUNTOS_RECHAZO", "0")),
}

PORT = int(os.getenv("PORT", "5000"))
CAMERA_INDEX = int(os.getenv("CAMERA_INDEX", "0"))

# ---------------------------------------------------------------------------
# Inicialización de Firebase
# ---------------------------------------------------------------------------
cred = credentials.Certificate(FIREBASE_CREDENTIALS)
firebase_admin.initialize_app(cred)
db = firestore.client()

# ---------------------------------------------------------------------------
# Inicialización de Flask
# ---------------------------------------------------------------------------
app = Flask(__name__)
CORS(app)


# ---------------------------------------------------------------------------
# Funciones auxiliares
# ---------------------------------------------------------------------------
def normalizar_clase(clase_predicha: str) -> str:
    """
    Normaliza el nombre de la clase devuelta por Roboflow a uno de los
    3 valores esperados: 'plastico', 'carton', 'rechazo'.

    Ajustar este mapeo según las clases reales con las que se entrenó
    el modelo "residuos-reciclaje" en Roboflow.
    """
    clase = clase_predicha.strip().lower()

    mapeo = {
        "plastico": "plastico",
        "plástico": "plastico",
        "plastic": "plastico",
        "botella": "plastico",
        "carton": "carton",
        "cartón": "carton",
        "cardboard": "carton",
        "caja": "carton",
        "rechazo": "rechazo",
        "basura": "rechazo",
        "trash": "rechazo",
        "otro": "rechazo",
    }

    return mapeo.get(clase, "rechazo")


def clasificar_imagen(imagen_bytes: bytes) -> dict:
    """
    Envía la imagen (bytes) a Roboflow y devuelve la mejor predicción.

    Retorna un dict:
        {
            "material": "plastico" | "carton" | "rechazo",
            "confianza": float,
            "clase_original": str,
            "raw": <respuesta completa de Roboflow>
        }
    """
    img_b64 = base64.b64encode(imagen_bytes).decode("utf-8")

    response = requests.post(
        ROBOFLOW_URL,
        data=img_b64,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=15,
    )
    response.raise_for_status()
    data = response.json()

    predicciones = data.get("predictions", [])

    if not predicciones:
        return {
            "material": "rechazo",
            "confianza": 0.0,
            "clase_original": None,
            "raw": data,
        }

    # Tomamos la predicción con mayor confianza
    mejor = max(predicciones, key=lambda p: p.get("confidence", 0))
    confianza = mejor.get("confidence", 0.0)
    clase_original = mejor.get("class", "rechazo")

    if confianza < CONFIDENCE_THRESHOLD:
        material = "rechazo"
    else:
        material = normalizar_clase(clase_original)

    return {
        "material": material,
        "confianza": confianza,
        "clase_original": clase_original,
        "raw": data,
    }


def capturar_foto() -> bytes:
    """
    Captura un frame desde la webcam y lo devuelve como bytes JPEG.
    """
    cap = cv2.VideoCapture(CAMERA_INDEX)

    if not cap.isOpened():
        raise RuntimeError("No se pudo acceder a la cámara")

    # Descartar algunos frames iniciales para que la cámara enfoque/ajuste
    for _ in range(5):
        cap.read()

    ok, frame = cap.read()
    cap.release()

    if not ok:
        raise RuntimeError("No se pudo capturar la imagen de la cámara")

    ok, buffer = cv2.imencode(".jpg", frame)
    if not ok:
        raise RuntimeError("No se pudo codificar la imagen capturada")

    return buffer.tobytes()


def obtener_usuario(codigo: str):
    """
    Busca el documento del usuario por código de 4 dígitos.
    Retorna el DocumentSnapshot o None si no existe.
    """
    doc_ref = db.collection("usuarios").document(codigo)
    doc = doc_ref.get()
    return doc_ref, doc


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    """Pantalla simple para la PC (ingreso de código + botón tomar foto)."""
    return render_template("index.html")


@app.route("/api/validar_codigo", methods=["POST"])
def validar_codigo():
    """
    Body JSON: { "codigo": "1234" }

    Verifica que el código exista en Firestore (colección "usuarios").
    """
    data = request.get_json(force=True)
    codigo = str(data.get("codigo", "")).strip()

    if not codigo or len(codigo) != 4 or not codigo.isdigit():
        return jsonify({"valido": False, "error": "Código inválido"}), 400

    _, doc = obtener_usuario(codigo)

    if not doc.exists:
        return jsonify({"valido": False, "error": "Código no encontrado"}), 404

    return jsonify({
        "valido": True,
        "codigo": codigo,
        "puntos": doc.to_dict().get("puntos", 0),
    })


@app.route("/api/clasificar", methods=["POST"])
def clasificar():
    """
    Body JSON: { "codigo": "1234" }

    1. Valida el código.
    2. Toma una foto con la webcam.
    3. Clasifica con Roboflow.
    4. Acredita puntos en Firestore y guarda la transacción.

    Respuesta JSON con el resultado de la clasificación y el nuevo saldo.
    """
    data = request.get_json(force=True)
    codigo = str(data.get("codigo", "")).strip()

    if not codigo or len(codigo) != 4 or not codigo.isdigit():
        return jsonify({"error": "Código inválido"}), 400

    user_ref, user_doc = obtener_usuario(codigo)

    if not user_doc.exists:
        return jsonify({"error": "Código no encontrado"}), 404

    # 1. Capturar foto
    try:
        imagen_bytes = capturar_foto()
    except RuntimeError as e:
        return jsonify({"error": f"Error de cámara: {e}"}), 500

    # 2. Clasificar con Roboflow
    try:
        resultado = clasificar_imagen(imagen_bytes)
    except requests.RequestException as e:
        return jsonify({"error": f"Error al consultar Roboflow: {e}"}), 502

    material = resultado["material"]
    confianza = resultado["confianza"]
    puntos_ganados = PUNTOS_POR_MATERIAL.get(material, 0)

    # 3. Acreditar puntos en Firestore
    nuevo_saldo = user_doc.to_dict().get("puntos", 0) + puntos_ganados
    user_ref.update({"puntos": nuevo_saldo})

    # 4. Registrar transacción
    db.collection("transacciones").add({
        "codigo": codigo,
        "material": material,
        "claseOriginal": resultado["clase_original"],
        "confianza": confianza,
        "puntosGanados": puntos_ganados,
        "timestamp": datetime.datetime.utcnow(),
    })

    return jsonify({
        "codigo": codigo,
        "material": material,
        "claseOriginal": resultado["clase_original"],
        "confianza": confianza,
        "puntosGanados": puntos_ganados,
        "nuevoSaldo": nuevo_saldo,
    })


@app.route("/api/foto_preview", methods=["GET"])
def foto_preview():
    """
    Endpoint auxiliar (opcional) para probar la cámara sin clasificar:
    devuelve la imagen JPEG capturada.
    """
    try:
        imagen_bytes = capturar_foto()
    except RuntimeError as e:
        return jsonify({"error": f"Error de cámara: {e}"}), 500

    return Response(imagen_bytes, mimetype="image/jpeg")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT, debug=True)
