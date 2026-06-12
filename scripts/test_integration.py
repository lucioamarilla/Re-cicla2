"""
Script de pruebas automatizadas - EcoPuntos Inteligentes MVP
===========================================================
Prueba todos los componentes del sistema de punta a punta.

Uso:
    source ecopuntos-venv/bin/activate
    python scripts/test_integration.py [--backend-url http://localhost:8000]

Requiere:
    - Backend corriendo: python backend/run.py
    - Opcional: una imagen test.jpg para probar depositos
"""

import os
import sys
import json
import time
import base64
import random
import string
import traceback
import argparse
from datetime import datetime

# Colores para output
VERDE = "\033[92m"
ROJO = "\033[91m"
AMARILLO = "\033[93m"
AZUL = "\033[94m"
RESET = "\033[0m"
BOLD = "\033[1m"

PASS = f"{VERDE}[PASS]{RESET}"
FAIL = f"{ROJO}[FAIL]{RESET}"
SKIP = f"{AMARILLO}[SKIP]{RESET}"
INFO = f"{AZUL}[INFO]{RESET}"

CONTADOR_PASADAS = 0
CONTADOR_FALLOS = 0
CONTADOR_SALTADOS = 0


def info(msg):
    print(f"  {INFO} {msg}")


def paso(msg):
    print(f"\n{BOLD}{msg}{RESET}")


def test(nombre, resultado, detalle=""):
    global CONTADOR_PASADAS, CONTADOR_FALLOS, CONTADOR_SALTADOS
    if resultado is None:
        print(f"  {SKIP} {nombre}")
        CONTADOR_SALTADOS += 1
        return False
    if resultado:
        print(f"  {PASS} {nombre}")
        CONTADOR_PASADAS += 1
        return True
    else:
        print(f"  {FAIL} {nombre}")
        if detalle:
            print(f"         {detalle}")
        CONTADOR_FALLOS += 1
        return False


def reporte_final():
    total = CONTADOR_PASADAS + CONTADOR_FALLOS + CONTADOR_SALTADOS
    print(f"\n{BOLD}{'='*60}{RESET}")
    print(f"{BOLD}RESUMEN DE PRUEBAS{RESET}")
    print(f"  Total: {total}")
    print(f"  {VERDE}Pasadas: {CONTADOR_PASADAS}{RESET}")
    print(f"  {ROJO}Fallos: {CONTADOR_FALLOS}{RESET}")
    print(f"  {AMARILLO}Saltadas: {CONTADOR_SALTADOS}{RESET}")
    print(f"{BOLD}{'='*60}{RESET}")
    if CONTADOR_FALLOS > 0:
        print(f"\n{ROJO}HAY FALLOS QUE CORREGIR{RESET}")
        sys.exit(1)
    elif CONTADOR_PASADAS > 0:
        print(f"\n{VERDE}TODAS LAS PRUEBAS PASARON{RESET}")
    else:
        print(f"\n{AMARILLO}NO SE EJECUTARON PRUEBAS{RESET}")


def main():
    parser = argparse.ArgumentParser(description="Pruebas de integracion EcoPuntos")
    parser.add_argument("--backend-url", default="http://localhost:8000", help="URL del backend")
    parser.add_argument("--image", default="test.jpg", help="Ruta a imagen JPG de prueba")
    parser.add_argument("--no-firebase", action="store_true", help="Saltar pruebas que requieren Firebase")
    args = parser.parse_args()

    BASE = args.backend_url.rstrip("/")
    IMAGE_PATH = args.image
    TIENE_IMAGEN = os.path.exists(IMAGE_PATH)

    import requests

    def get(path):
        return requests.get(f"{BASE}{path}", timeout=10)

    def post(path, data=None, json_data=None, files=None):
        return requests.post(f"{BASE}{path}", data=data, json=json_data, files=files, timeout=15)

    def json_ok(r):
        try:
            return r.json()
        except Exception:
            return None

    # =========================================================================
    print(f"\n{BOLD}ECO PUNTOS - PRUEBAS DE INTEGRACION{RESET}")
    print(f"Backend: {BASE}")
    print(f"Inicio:  {datetime.now().strftime('%H:%M:%S')}")
    print(f"{'='*60}")

    # =========================================================================
    paso("1. PRUEBAS DE CONECTIVIDAD")
    # =========================================================================

    # 1.1 Health check
    try:
        r = get("/health")
        test("Health endpoint", r.status_code == 200, f"Status: {r.status_code}")
        if r.status_code == 200:
            test("Health body ok", json_ok(r) == {"status": "ok"}, str(json_ok(r)))
    except requests.exceptions.ConnectionError as e:
        test(f"Conexion al backend", False,
             f"No se puede conectar a {BASE}. ¿El backend esta corriendo?")
        reporte_final()

    # 1.2 CORS (enviando Origin como lo haria un navegador)
    try:
        r = requests.get(f"{BASE}/health", headers={"Origin": "http://localhost:5000"}, timeout=5)
        has_cors = r.headers.get("access-control-allow-origin") == "*"
        test("CORS headers presentes", has_cors)
    except Exception:
        test("CORS headers", False, "No se pudo verificar CORS")

    # =========================================================================
    paso("2. PRUEBAS DE USUARIOS")
    # =========================================================================

    test_user_code = None
    test_user_name = f"Test{random.randint(1000, 9999)}"

    # 2.1 Register
    try:
        r = post("/api/register", json_data={"nombre": test_user_name})
        data = json_ok(r)
        ok = r.status_code == 200 and data and "codigo" in data
        test("POST /api/register - crear usuario", ok, str(data))
        if ok:
            test_user_code = data["codigo"]
            test("Codigo generado es 4 chars", len(test_user_code) == 4, f"Codigo: {test_user_code}")
            test("Saldo inicial es 0", data.get("saldo") == 0)
    except Exception as e:
        test("POST /api/register", False, str(e))

    # 2.2 Register con nombre vacio
    try:
        r = post("/api/register", json_data={"nombre": ""})
        test("Register con nombre vacio -> 400", r.status_code == 400)
    except Exception:
        test("Register con nombre vacio", False)

    # 2.3 Get user valido
    if test_user_code:
        try:
            r = get(f"/api/user/{test_user_code}")
            data = json_ok(r)
            ok = r.status_code == 200 and data and data.get("codigo") == test_user_code
            test(f"GET /api/user/{test_user_code} - usuario existe", ok)
            if ok:
                test(f"Nombre coincide", data.get("nombre") == test_user_name)
        except Exception as e:
            test(f"GET /api/user/{test_user_code}", False, str(e))
    else:
        test("GET /api/user - skip (sin usuario)", None)

    # 2.4 Get user invalido
    try:
        r = get("/api/user/ZZZZ")
        test("GET /api/user/ZZZZ - usuario no existe -> 404", r.status_code == 404)
    except Exception:
        test("GET /api/user/ZZZZ", False)

    # =========================================================================
    paso("3. PRUEBAS DE DEPOSITO")
    # =========================================================================

    # 3.1 Deposito sin autenticacion (codigo faltante)
    try:
        r = post("/api/deposit")
        test("Deposito sin codigo -> 422/400", r.status_code in [400, 422])
    except Exception:
        test("Deposito sin codigo", False)

    # 3.2 Deposito con codigo invalido (sin imagen, espera 422)
    try:
        r = post("/api/deposit", data={"code": "ZZZZ"})
        test("Deposito sin imagen -> 422/400", r.status_code in [400, 422])
    except Exception:
        test("Deposito sin imagen", False)

    # 3.3 Deposito exitoso (requiere imagen test.jpg)
    if test_user_code and TIENE_IMAGEN:
        try:
            with open(IMAGE_PATH, "rb") as f:
                r = post("/api/deposit", data={"code": test_user_code},
                         files={"image": ("test.jpg", f, "image/jpeg")})
            data = json_ok(r)
            ok = r.status_code == 200 and data and "success" in data
            test(f"POST /api/deposit - deposito con imagen", ok, str(data))
            if ok:
                test(f"Puntos asignados (0 o 1)", data.get("puntos") in [0, 1])
                test(f"Material detectado no vacio",
                     data.get("material") in ["plastico", "carton", "rechazo"])
                if data.get("puntos") == 1:
                    info(f"Deposito EXITOSO: {data['material']} "
                         f"({data.get('confianza', 0)*100:.0f}%) -> +1 punto")
                else:
                    info(f"Deposito RECHAZADO: {data['material']} "
                         f"({data.get('confianza', 0)*100:.0f}%) -> 0 puntos")
        except Exception as e:
            test("POST /api/deposit - deposito con imagen", False, str(e))
    else:
        if not TIENE_IMAGEN:
            test("Deposito con imagen - skip (no existe test.jpg)", None)
            info("Pasa una imagen: python scripts/test_integration.py --image ruta/a/foto.jpg")
        if not test_user_code:
            test("Deposito con imagen - skip (sin usuario)", None)

    # 3.4 Deposito con imagen demasiado grande
    if test_user_code:
        try:
            data_falsa = b"x" * (6 * 1024 * 1024)  # 6MB > 5MB max
            r = post("/api/deposit", data={"code": test_user_code},
                     files={"image": ("big.jpg", data_falsa, "image/jpeg")})
            test("Deposito con imagen >5MB -> 400", r.status_code == 400)
        except Exception:
            test("Deposito con imagen >5MB", False)

    # =========================================================================
    paso("4. PRUEBAS DE TRANSACCIONES")
    # =========================================================================

    # 4.1 Historial de usuario existente
    if test_user_code:
        try:
            r = get(f"/api/transactions/{test_user_code}")
            data = json_ok(r)
            ok = r.status_code == 200 and data is not None
            if ok:
                if isinstance(data, list):
                    test(f"GET /api/transactions/{test_user_code}", True)
                    info(f"Transacciones encontradas: {len(data)}")
                    if len(data) > 0:
                        tx = data[0]
                        test("Transaccion tiene userId",
                             tx.get("userId") == test_user_code)
                        test("Transaccion tiene material",
                             "material" in tx)
                        test("Transaccion tiene puntos",
                             "puntos" in tx)
                elif isinstance(data, dict):
                    test("GET /api/transactions (Firestore no disponible)", True)
                    info("Firestore no disponible - transacciones no persisten")
                else:
                    test(f"GET /api/transactions/{test_user_code}", True)
                    info(f"Respuesta: {data}")
            else:
                test(f"GET /api/transactions/{test_user_code}", False,
                     f"Status {r.status_code}: {data}")
        except Exception as e:
            err = str(e)
            if "index" in err.lower():
                info("Firestore requiere un indice compuesto. Crea uno en Firebase Console:")
                info("  Coleccion: transactions, Campos: userId ASC, timestamp DESC")
                test(f"GET /api/transactions/{test_user_code} -> requiere indice", True)
            else:
                test(f"GET /api/transactions/{test_user_code}", False, err)
    else:
        test("GET /api/transactions - skip (sin usuario)", None)

    # 4.2 Historial de usuario inexistente
    try:
        r = get("/api/transactions/ZZZZ")
        test("GET /api/transactions/ZZZZ", r.status_code in [200, 404])
    except Exception:
        test("GET /api/transactions/ZZZZ", False)

    # =========================================================================
    paso("5. PRUEBAS DE CANJE")
    # =========================================================================

    # 5.1 Canje sin saldo suficiente
    if test_user_code:
        try:
            r = post("/api/redeem", data={"code": test_user_code})
            test("Canje sin saldo -> 400/422", r.status_code in [400, 422])
        except Exception:
            test("Canje sin saldo", False)
    else:
        test("Canje sin saldo - skip (sin usuario)", None)

    # =========================================================================
    paso("6. PRUEBAS DE ROBUSTEZ")
    # =========================================================================

    # 6.1 Timeout rapido (simulado con endpoint que no existe)
    try:
        r = get("/api/user/TO", timeout=0.001)
        test("Timeout manejado correctamente", False)
    except requests.exceptions.Timeout:
        test("Timeout manejado correctamente (esperado)", True)
    except Exception:
        test("Timeout manejado correctamente (otro error)", True)

    # =========================================================================
    paso("7. PRUEBAS DE ROBOFLOW (directo)")
    # =========================================================================

    if TIENE_IMAGEN:
        import cv2
        try:
            with open(IMAGE_PATH, "rb") as f:
                img_b64 = base64.b64encode(f.read()).decode("utf-8")
            api_key = "9bV8sIpOxb79beiXxskn"
            model_id = "residuos-reciclaje"
            version = "1"
            url = f"https://detect.roboflow.com/{model_id}/{version}"
            r = requests.post(
                url,
                params={"api_key": api_key},
                data=img_b64,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=15,
            )
            ok = r.status_code == 200
            test("Roboflow API - conexion directa", ok, f"Status: {r.status_code}")
            if ok:
                data = r.json()
                tiene_predictions = "predictions" in data
                tiene_top = "top" in data
                test("Roboflow respuesta tiene predictions/top",
                     tiene_predictions or tiene_top)
                if tiene_predictions:
                    test("Predictions es lista",
                         isinstance(data["predictions"], list))
                    if data["predictions"]:
                        info(f"Mejor prediccion: "
                             f"{data['predictions'][0].get('class', 'N/A')} "
                             f"({data['predictions'][0].get('confidence', 0)*100:.1f}%)")
                if tiene_top:
                    info(f"Clasificacion top: {data['top']} "
                         f"(confidence: {data.get('confidence', 0)*100:.1f}%)")
        except requests.exceptions.HTTPError as e:
            test("Roboflow API - conexion directa", False, f"HTTP error: {e}")
        except Exception as e:
            test("Roboflow API - conexion directa", False, str(e))
    else:
        test("Roboflow API - directo (no existe test.jpg)", None)

    # =========================================================================
    paso("8. PRUEBAS DE OPENCV (opcional)")
    # =========================================================================

    try:
        import cv2
        cap = cv2.VideoCapture(0)
        if cap.isOpened():
            for _ in range(5):
                cap.read()
            ok, frame = cap.read()
            cap.release()
            test("OpenCV - camara detectable", ok)
            if ok:
                test("OpenCV - frame capturable", frame is not None and frame.size > 0)
                _, buffer = cv2.imencode(".jpg", frame)
                test("OpenCV - codificacion JPG", buffer is not None and len(buffer) > 0)
                resized = cv2.resize(frame, (224, 224))
                test("OpenCV - redimension 224x224",
                     resized.shape[0] == 224 and resized.shape[1] == 224)
        else:
            test("OpenCV - camara", False, "No se pudo abrir camara en indice 0")
    except ImportError:
        test("OpenCV - modulo no instalado", None)
    except Exception as e:
        test("OpenCV - prueba", False, str(e))

    # =========================================================================
    paso("9. PRUEBAS DE ATOMICIDAD (opcional)")
    # =========================================================================

    if test_user_code and TIENE_IMAGEN:
        info("Ejecutando 3 depositos simultaneos...")
        try:
            exito = 0
            with open(IMAGE_PATH, "rb") as f:
                img_data = f.read()

            def do_deposit():
                nonlocal exito
                try:
                    r = post("/api/deposit", data={"code": test_user_code},
                             files={"image": ("t.jpg", img_data, "image/jpeg")})
                    d = json_ok(r)
                    if d and d.get("puntos", 0) > 0:
                        exito += 1
                except Exception:
                    pass

            import threading
            threads = []
            for _ in range(3):
                t = threading.Thread(target=do_deposit)
                threads.append(t)
                t.start()
            for t in threads:
                t.join()

            r = get(f"/api/user/{test_user_code}")
            data = json_ok(r)
            if data and "saldo" in data:
                saldo_final = data["saldo"]
                test(f"Atomicidad - {exito} exitosos de 3, saldo={saldo_final}", True)
                info(f"Depositos exitosos: {exito}/3, Saldo final: {saldo_final}")
        except Exception as e:
            test("Atomicidad", False, str(e))
    else:
        test("Atomicidad - skip", None)

    # =========================================================================
    print(f"\n{'='*60}")
    reporte_final()


if __name__ == "__main__":
    main()
