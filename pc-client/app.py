import os
import base64
import atexit
import requests
from flask import Flask, jsonify, request, render_template, Response
from dotenv import load_dotenv
from camera import camera

load_dotenv()

app = Flask(__name__, static_folder="static", template_folder="templates")
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000").rstrip("/")
FLASK_PORT = int(os.getenv("FLASK_PORT", "5001"))

atexit.register(camera.release)


def generar_frames():
    while True:
        frame = camera.get_frame_jpeg()
        if frame is None:
            continue
        yield (b"--frame\r\n" b"Content-Type: image/jpeg\r\n\r\n" + frame + b"\r\n")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/video_feed")
def video_feed():
    return Response(generar_frames(), mimetype="multipart/x-mixed-replace; boundary=frame")


@app.route("/validate", methods=["POST"])
def validate():
    data = request.get_json(force=True)
    uid = data.get("uid", "").strip()
    if not uid:
        return jsonify({"valido": False, "error": "UID inválido"}), 400
    try:
        resp = requests.get(f"{BACKEND_URL}/api/user/{uid}", timeout=5)
        if resp.status_code == 200:
            user = resp.json()
            return jsonify({"valido": True, "nombre": user["nombre"], "saldo": user["saldo"]})
        return jsonify({"valido": False, "error": "UID no encontrado"}), 404
    except requests.RequestException:
        return jsonify({"valido": False, "error": "Error de conexion con el servidor"}), 502


@app.route("/capturar", methods=["POST"])
def capturar():
    try:
        img_b64 = camera.capture_base64()
        return jsonify({"success": True, "image": img_b64, "width": 224, "height": 224})
    except RuntimeError as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/clasificar", methods=["POST"])
def clasificar():
    data = request.get_json(force=True)
    img_b64 = data.get("imagen_base64")
    uid = data.get("uid", "").strip()
    nombre = data.get("nombre", "")
    if not img_b64 or not uid or not nombre:
        return jsonify({"error": "Faltan datos (imagen_base64, uid, nombre)"}), 400
    try:
        resp = requests.post(
            f"{BACKEND_URL}/api/deposit",
            data={"uid": uid},
            files={"image": ("capture.jpg", base64.b64decode(img_b64), "image/jpeg")},
            timeout=15,
        )
        return jsonify(resp.json()), resp.status_code
    except requests.exceptions.Timeout:
        return jsonify({"error": "timeout"}), 504
    except requests.RequestException as e:
        return jsonify({"error": "error_api", "detalle": str(e)}), 502


@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "recurso_no_encontrado"}), 404


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=FLASK_PORT, debug=True)
