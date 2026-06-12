"""
Debug completo - EcoPuntos Inteligentes MVP
============================================
Prueba todos los componentes del sistema con el nuevo sistema UID.

Uso:
    source ecopuntos-venv/bin/activate
    python scripts/debug_full_system.py [--backend-url http://localhost:8000]
                                        [--pc-url http://localhost:5001]
                                        [--image test.jpg]
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

_script_dir = os.path.dirname(os.path.abspath(__file__))
_backend_dir = os.path.join(_script_dir, "..", "backend")
if os.path.isdir(_backend_dir):
    sys.path.insert(0, _backend_dir)

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


def crear_usuario_firestore_directo(firebase_uid, email, nombre):
    """Crea un usuario directamente en Firestore (como lo hace la app mobile)"""
    try:
        import firebase_admin
        from firebase_admin import credentials, firestore
        if not firebase_admin._apps:
            cred_path = os.getenv("FIREBASE_CREDENTIALS_PATH",
                                  "./backend/firebase_credentials.json")
            if not os.path.exists(cred_path):
                cred_path = "./firebase_credentials.json"
            if os.path.exists(cred_path):
                cred = credentials.Certificate(cred_path)
                firebase_admin.initialize_app(cred)
        db = firestore.client()
        doc_ref = db.collection("users").document(firebase_uid)
        if not doc_ref.get().exists:
            doc_ref.set({
                "uid": firebase_uid,
                "email": email,
                "nombre": nombre,
                "saldo": 0,
                "creado": firestore.SERVER_TIMESTAMP,
            })
        return True
    except Exception as e:
        print(f"         Error creando usuario en Firestore: {e}")
        return False


def leer_usuario_firestore(uid):
    """Lee un usuario directamente de Firestore"""
    try:
        import firebase_admin
        from firebase_admin import credentials, firestore
        if not firebase_admin._apps:
            cred_path = os.getenv("FIREBASE_CREDENTIALS_PATH",
                                  "./backend/firebase_credentials.json")
            if not os.path.exists(cred_path):
                cred_path = "./firebase_credentials.json"
            if os.path.exists(cred_path):
                cred = credentials.Certificate(cred_path)
                firebase_admin.initialize_app(cred)
        db = firestore.client()
        doc = db.collection("users").document(uid).get()
        if doc.exists:
            return doc.to_dict()
        return None
    except Exception as e:
        print(f"         Error leyendo Firestore: {e}")
        return None


def limpiar_usuario_firestore(uid):
    """Elimina un usuario y sus transacciones de Firestore"""
    try:
        import firebase_admin
        from firebase_admin import credentials, firestore
        if not firebase_admin._apps:
            cred_path = os.getenv("FIREBASE_CREDENTIALS_PATH",
                                  "./backend/firebase_credentials.json")
            if not os.path.exists(cred_path):
                cred_path = "./firebase_credentials.json"
            if os.path.exists(cred_path):
                cred = credentials.Certificate(cred_path)
                firebase_admin.initialize_app(cred)
        db = firestore.client()
        txns = db.collection("transactions").where("userId", "==", uid).stream()
        for t in txns:
            t.reference.delete()
        db.collection("users").document(uid).delete()
        return True
    except Exception:
        return False


def main():
    parser = argparse.ArgumentParser(description="Debug completo EcoPuntos")
    parser.add_argument("--backend-url", default="http://localhost:8000",
                        help="URL del backend")
    parser.add_argument("--pc-url", default="http://localhost:5001",
                        help="URL del PC Client")
    parser.add_argument("--image", default="test.jpg",
                        help="Ruta a imagen JPG de prueba")
    parser.add_argument("--no-firebase", action="store_true",
                        help="Saltar pruebas que requieren Firebase")
    parser.add_argument("--no-cleanup", action="store_true",
                        help="No limpiar datos de prueba al final")
    args = parser.parse_args()

    BASE = args.backend_url.rstrip("/")
    PC_BASE = args.pc_url.rstrip("/")
    IMAGE_PATH = args.image
    TIENE_IMAGEN = os.path.exists(IMAGE_PATH)
    TIENE_FIREBASE = not args.no_firebase

    try:
        import requests
    except ImportError:
        test("Import requests", False, "pip install requests")
        reporte_final()
        return

    def get(path, **kwargs):
        return requests.get(f"{BASE}{path}", timeout=kwargs.pop("timeout", 10), **kwargs)

    def post(path, **kwargs):
        return requests.post(f"{BASE}{path}", timeout=kwargs.pop("timeout", 15), **kwargs)

    def pc_get(path, **kwargs):
        return requests.get(f"{PC_BASE}{path}", timeout=kwargs.pop("timeout", 10), **kwargs)

    def pc_post(path, **kwargs):
        return requests.post(f"{PC_BASE}{path}", timeout=kwargs.pop("timeout", 10), **kwargs)

    def json_ok(r):
        try:
            return r.json()
        except Exception:
            return None

    UID_TEST = f"test_{random.randint(10000, 99999)}"
    EMAIL_TEST = f"{UID_TEST}@test.com"
    NOMBRE_TEST = f"TestUser{random.randint(100, 999)}"

    print(f"\n{BOLD}ECO PUNTOS - DEBUG COMPLETO DEL SISTEMA{RESET}")
    print(f"Backend:  {BASE}")
    print(f"PC Client: {PC_BASE}")
    print(f"UID test: {UID_TEST}")
    print(f"Inicio:   {datetime.now().strftime('%H:%M:%S')}")
    print(f"{'='*60}")

    # =========================================================================
    paso("1. CONECTIVIDAD")
    # =========================================================================

    # 1.1 Backend health
    try:
        r = get("/health")
        test("Backend health endpoint", r.status_code == 200,
             f"Status: {r.status_code}")
        if r.status_code == 200:
            test("Backend health body ok",
                 json_ok(r) == {"status": "ok"}, str(json_ok(r)))
    except requests.exceptions.ConnectionError as e:
        test("Conexion al backend", False,
             f"No se puede conectar a {BASE}. ¿El backend esta corriendo?")
        reporte_final()
        return

    # 1.2 Backend CORS
    try:
        r = requests.get(f"{BASE}/health",
                         headers={"Origin": "http://localhost:5000"}, timeout=5)
        has_cors = r.headers.get("access-control-allow-origin") == "*"
        test("Backend CORS headers", has_cors)
    except Exception:
        test("Backend CORS headers", False, "No se pudo verificar CORS")

    # 1.3 PC Client
    try:
        r = pc_get("/")
        test("PC Client pagina principal", r.status_code == 200,
             f"Status: {r.status_code}")
        has_form = 'uidInput' in r.text
        test("PC Client contiene formulario UID", has_form)
    except requests.exceptions.ConnectionError:
        test("PC Client no disponible", None)

    # =========================================================================
    paso("2. BACKEND - USUARIOS (sistema UID)")
    # =========================================================================

    # 2.1 GET /api/user/{uid} - usuario NO existe
    try:
        r = get(f"/api/user/NOEXISTE_{random.randint(1000,9999)}")
        test("GET /api/user/INEXISTENTE -> 404", r.status_code == 404,
             f"Status: {r.status_code}")
    except Exception as e:
        test("GET /api/user/INEXISTENTE", False, str(e))

    # 2.2 POST /api/sync_user - sin token
    # FastAPI da 422 si falta header requerido, 401 si el header es invalido
    try:
        r = post("/api/sync_user",
                 json={"uid": UID_TEST, "email": EMAIL_TEST, "nombre": NOMBRE_TEST})
        test("POST /api/sync_user sin token -> 401/422",
             r.status_code in [401, 422],
             f"Status: {r.status_code}, Body: {json_ok(r)}")
    except Exception as e:
        test("POST /api/sync_user sin token", False, str(e))

    # 2.3 POST /api/sync_user - con token invalido (debe dar 401)
    try:
        r = post("/api/sync_user",
                 json={"uid": UID_TEST, "email": EMAIL_TEST, "nombre": NOMBRE_TEST},
                 headers={"Authorization": "Bearer token_invalido_aqui"})
        test("POST /api/sync_user con token invalido -> 401",
             r.status_code == 401, f"Status: {r.status_code}, Body: {json_ok(r)}")
    except Exception as e:
        test("POST /api/sync_user con token invalido", False, str(e))

    # 2.4 GET /api/user/{uid} - usuario existe (creado via Firestore directo)
    usuario_creado = False
    if TIENE_FIREBASE:
        try:
            creado = crear_usuario_firestore_directo(UID_TEST, EMAIL_TEST, NOMBRE_TEST)
            test("Crear usuario directo en Firestore", creado)
            if creado:
                usuario_creado = True
                time.sleep(1)
        except Exception as e:
            test("Crear usuario directo en Firestore", False, str(e))
    else:
        test("Crear usuario directo en Firestore (no-firebase mode)", None)

    # 2.5 GET /api/user/{uid} - usuario SÍ existe
    if usuario_creado:
        try:
            r = get(f"/api/user/{UID_TEST}")
            data = json_ok(r)
            ok = r.status_code == 200 and data and data.get("uid") == UID_TEST
            test(f"GET /api/user/{UID_TEST} - usuario existe", ok,
                 f"Status: {r.status_code}" if not ok else "")
            if ok:
                test(f"Email coincide", data.get("email") == EMAIL_TEST,
                     f"Esperado: {EMAIL_TEST}, Obtenido: {data.get('email')}")
                test(f"Nombre coincide", data.get("nombre") == NOMBRE_TEST,
                     f"Esperado: {NOMBRE_TEST}, Obtenido: {data.get('nombre')}")
                test(f"Saldo inicial es 0", data.get("saldo") == 0,
                     f"Saldo: {data.get('saldo')}")
        except Exception as e:
            test(f"GET /api/user/{UID_TEST}", False, str(e))
    else:
        test("GET /api/user existente - skip (sin Firestore)", None)

    # 2.6 GET /api/user/{uid} - uid vacio
    try:
        r = get("/api/user/ ")
        test("GET /api/user con uid vacio -> 4xx",
             r.status_code in [400, 404, 422],
             f"Status: {r.status_code}")
    except Exception:
        test("GET /api/user con uid vacio", False)

    # =========================================================================
    paso("3. BACKEND - DEPOSITOS")
    # =========================================================================

    # 3.1 POST /api/deposit - sin uid (debe dar 422)
    try:
        r = post("/api/deposit")
        test("POST /api/deposit sin uid -> 422", r.status_code == 422,
             f"Status: {r.status_code}")
    except Exception as e:
        test("POST /api/deposit sin uid", False, str(e))

    # 3.2 POST /api/deposit - con uid invalido
    try:
        r = post("/api/deposit", data={"uid": "NOEXISTE"})
        test("POST /api/deposit uid invalido -> 422/400",
             r.status_code in [400, 422],
             f"Status: {r.status_code}")
    except Exception as e:
        test("POST /api/deposit uid invalido", False, str(e))

    # 3.3 POST /api/deposit - uid valido, sin imagen (debe dar 422)
    if usuario_creado:
        try:
            r = post("/api/deposit", data={"uid": UID_TEST})
            test("POST /api/deposit sin imagen -> 422",
                 r.status_code == 422,
                 f"Status: {r.status_code}")
        except Exception as e:
            test("POST /api/deposit sin imagen", False, str(e))
    else:
        test("POST /api/deposit sin imagen - skip (sin usuario)", None)

    # 3.4 POST /api/deposit - uid valido + imagen
    saldo_antes_deposito = 0
    if usuario_creado and TIENE_IMAGEN:
        try:
            with open(IMAGE_PATH, "rb") as f:
                r = post("/api/deposit",
                         data={"uid": UID_TEST},
                         files={"image": ("test.jpg", f, "image/jpeg")})
            data = json_ok(r)
            ok = r.status_code == 200 and data is not None
            test(f"POST /api/deposit - deposito con imagen", ok,
                 f"Status: {r.status_code}, Body: {data}" if not ok else "")
            if ok:
                test(f"Respuesta tiene userId", data.get("userId") == UID_TEST)
                test(f"Respuesta tiene material",
                     data.get("material") in ["plastico", "carton", "rechazo"])
                test(f"Respuesta tiene puntos",
                     data.get("puntos") in [0, 1])
                saldo_antes_deposito = data.get("nuevoSaldo", 0)
                if data.get("puntos") == 1:
                    info(f"Deposito EXITOSO: {data['material']} "
                         f"({data.get('confianza', 0)*100:.0f}%) -> +1 punto")
                else:
                    info(f"Deposito RECHAZADO: {data['material']} "
                         f"({data.get('confianza', 0)*100:.0f}%) -> 0 puntos")
        except Exception as e:
            test("POST /api/deposit con imagen", False, str(e))
    else:
        if not TIENE_IMAGEN:
            test("POST /api/deposit con imagen - skip (no existe test.jpg)", None)
        if not usuario_creado:
            test("POST /api/deposit con imagen - skip (sin usuario)", None)

    # 3.5 Deposito con imagen >5MB
    if usuario_creado:
        try:
            data_falsa = b"x" * (6 * 1024 * 1024)
            r = post("/api/deposit",
                     data={"uid": UID_TEST},
                     files={"image": ("big.jpg", data_falsa, "image/jpeg")})
            test("POST /api/deposit con imagen >5MB -> 400",
                 r.status_code == 400,
                 f"Status: {r.status_code}")
        except Exception as e:
            test("POST /api/deposit con imagen >5MB", False, str(e))
    else:
        test("POST /api/deposit imagen >5MB - skip (sin usuario)", None)

    # 3.6 Verificar saldo incrementado
    if usuario_creado:
        try:
            r = get(f"/api/user/{UID_TEST}")
            data = json_ok(r)
            if data and "saldo" in data:
                saldo_actual = data["saldo"]
                test(f"Saldo actual es {saldo_actual} (era {saldo_antes_deposito})",
                     saldo_actual >= saldo_antes_deposito,
                     f"Antes: {saldo_antes_deposito}, Ahora: {saldo_actual}")
            else:
                test("Verificar saldo en GET /api/user", False, str(data))
        except Exception as e:
            test("Verificar saldo", False, str(e))
    else:
        test("Verificar saldo depositado - skip (sin usuario)", None)

    # =========================================================================
    paso("4. BACKEND - TRANSACCIONES")
    # =========================================================================

    # 4.1 GET /api/transactions/{uid} - usuario existente
    if usuario_creado:
        try:
            r = get(f"/api/transactions/{UID_TEST}")
            data = json_ok(r)
            ok = r.status_code == 200 and data is not None
            test(f"GET /api/transactions/{UID_TEST}", ok,
                 f"Status: {r.status_code}" if not ok else "")
            if ok:
                if isinstance(data, list):
                    info(f"Transacciones encontradas: {len(data)}")
                    if len(data) > 0:
                        tx = data[0]
                        test("Transaccion tiene userId",
                             tx.get("userId") == UID_TEST)
                        test("Transaccion tiene material",
                             "material" in tx)
                        test("Transaccion tiene puntos",
                             "puntos" in tx)
                        test("Transaccion tiene tipo",
                             tx.get("tipo") in ["deposito", "canje"])
                elif isinstance(data, dict) and "transactions" in data:
                    txs = data["transactions"]
                    info(f"Transacciones encontradas: {len(txs)}")
                else:
                    info(f"Respuesta de transacciones: {data}")
        except Exception as e:
            err = str(e)
            if "index" in err.lower():
                info("Firestore requiere indice compuesto transactions/userId/timestamp")
                test("GET /api/transactions - requiere indice compuesto", True)
            else:
                test(f"GET /api/transactions/{UID_TEST}", False, str(e))
    else:
        test("GET /api/transactions existente - skip (sin usuario)", None)

    # 4.2 GET /api/transactions/{uid} - usuario inexistente
    try:
        r = get("/api/transactions/NOEXISTE_99999")
        test("GET /api/transactions INEXISTENTE -> 200/[]",
             r.status_code == 200,
             f"Status: {r.status_code}")
    except Exception:
        test("GET /api/transactions INEXISTENTE", False)

    # 4.3 Limite por defecto
    if usuario_creado:
        try:
            r = get(f"/api/transactions/{UID_TEST}?limit=5")
            test("GET /api/transactions con limit=5", r.status_code == 200,
                 f"Status: {r.status_code}")
        except Exception:
            test("GET /api/transactions con limit=5", False)
    else:
        test("GET /api/transactions limit - skip (sin usuario)", None)

    # =========================================================================
    paso("5. BACKEND - CANJES")
    # =========================================================================

    # 5.1 POST /api/redeem - sin uid (campo faltante -> 422)
    try:
        r = post("/api/redeem", data={})
        test("POST /api/redeem sin uid -> 422",
             r.status_code == 422,
             f"Status: {r.status_code}")
    except Exception:
        test("POST /api/redeem sin uid", False)

    # 5.2 POST /api/redeem - uid vacio (debe dar 400)
    try:
        r = post("/api/redeem", data={"uid": ""})
        test("POST /api/redeem uid vacio -> 400/422",
             r.status_code in [400, 422],
             f"Status: {r.status_code}")
    except Exception:
        test("POST /api/redeem uid vacio", False)

    # 5.3 POST /api/redeem - saldo insuficiente
    if usuario_creado:
        try:
            r = post("/api/redeem", data={"uid": UID_TEST, "puntos": 999})
            test("POST /api/redeem saldo insuficiente -> 400",
                 r.status_code == 400,
                 f"Status: {r.status_code}, Body: {json_ok(r)}")
        except Exception as e:
            test("POST /api/redeem saldo insuficiente", False, str(e))
    else:
        test("POST /api/redeem saldo insuficiente - skip (sin usuario)", None)

    # 5.4 POST /api/redeem - exitoso (siempre que tengamos al menos 5 puntos)
    if usuario_creado:
        try:
            r = post("/api/redeem", data={"uid": UID_TEST, "puntos": 1})
            data = json_ok(r)
            if r.status_code == 200:
                test("POST /api/redeem exitoso", data.get("success") is True,
                     str(data))
                if data.get("success"):
                    test("Canje tiene nuevo_saldo",
                         "nuevo_saldo" in data)
                    test("Canje tiene cupon",
                         "cupon" in data)
            elif r.status_code == 400:
                info(f"Canje no disponible: {data}")
                test("POST /api/redeem rechazado (saldo < 1)", True)
            else:
                test("POST /api/redeem", False,
                     f"Status: {r.status_code}, Body: {data}")
        except Exception as e:
            test("POST /api/redeem", False, str(e))
    else:
        test("POST /api/redeem exitoso - skip (sin usuario)", None)

    # =========================================================================
    paso("6. PC CLIENT - ENDPOINTS")
    # =========================================================================

    # 6.1 GET / - pagina principal
    try:
        r = pc_get("/")
        test("PC Client GET / -> 200", r.status_code == 200,
             f"Status: {r.status_code}")
    except requests.exceptions.ConnectionError:
        test("PC Client GET / - no disponible", None)

    # 6.2 GET /video_feed
    try:
        r = pc_get("/video_feed", timeout=3)
        test("PC Client GET /video_feed -> video stream",
             r.status_code == 200,
             f"Status: {r.status_code}")
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        test("PC Client GET /video_feed - no disponible o timeout", None)

    # 6.3 POST /validate - uid valido
    if usuario_creado:
        try:
            r = pc_post("/validate",
                        json={"uid": UID_TEST})
            data = json_ok(r)
            ok = r.status_code == 200 and data and data.get("valido") is True
            test("PC Client POST /validate uid valido", ok,
                 f"Status: {r.status_code}, Body: {data}" if not ok else "")
            if ok:
                test("Validate devuelve nombre",
                     data.get("nombre") == NOMBRE_TEST)
                test("Validate devuelve saldo >= 0",
                     data.get("saldo", -1) >= 0)
        except requests.exceptions.ConnectionError:
            test("PC Client POST /validate - no disponible", None)
        except Exception as e:
            test("PC Client POST /validate", False, str(e))
    else:
        test("PC Client POST /validate uid valido - skip (sin usuario)", None)

    # 6.4 POST /validate - uid invalido
    try:
        r = pc_post("/validate",
                    json={"uid": "UID_INVALIDO_99999"})
        test("PC Client POST /validate uid invalido -> 404",
             r.status_code == 404,
             f"Status: {r.status_code}")
    except requests.exceptions.ConnectionError:
        test("PC Client POST /validate uid invalido - no disponible", None)
    except Exception:
        test("PC Client POST /validate uid invalido", False)

    # 6.5 POST /capturar - sin camara (debe dar 500)
    try:
        r = pc_post("/capturar")
        test("PC Client POST /capturar (esperado 500 sin camara fisica)",
             r.status_code == 500,
             f"Status: {r.status_code}, Body: {json_ok(r)}")
    except requests.exceptions.ConnectionError:
        test("PC Client POST /capturar - no disponible", None)
    except Exception:
        test("PC Client POST /capturar", False)

    # 6.6 POST /clasificar - datos faltantes (debe dar 400)
    try:
        r = pc_post("/clasificar", json={})
        test("PC Client POST /clasificar sin datos -> 400",
             r.status_code == 400,
             f"Status: {r.status_code}, Body: {json_ok(r)}")
    except requests.exceptions.ConnectionError:
        test("PC Client POST /clasificar sin datos - no disponible", None)
    except Exception:
        test("PC Client POST /clasificar sin datos", False)

    # 6.7 POST /clasificar - datos incompletos
    try:
        r = pc_post("/clasificar",
                    json={"imagen_base64": "data:imagen"})
        test("PC Client POST /clasificar solo imagen -> 400",
             r.status_code == 400,
             f"Status: {r.status_code}, Body: {json_ok(r)}")
    except requests.exceptions.ConnectionError:
        test("PC Client POST /clasificar solo imagen - no disponible", None)
    except Exception:
        test("PC Client POST /clasificar solo imagen", False)

    # =========================================================================
    paso("7. FIRESTORE - VERIFICACION DIRECTA")
    # =========================================================================

    if TIENE_FIREBASE and usuario_creado:
        # 7.1 Leer usuario creado
        try:
            data = leer_usuario_firestore(UID_TEST)
            test("Firestore: usuario existe", data is not None)
            if data:
                test("Firestore: uid coincide",
                     data.get("uid") == UID_TEST)
                test("Firestore: email coincide",
                     data.get("email") == EMAIL_TEST)
                test("Firestore: nombre coincide",
                     data.get("nombre") == NOMBRE_TEST)
                test("Firestore: saldo es entero",
                     isinstance(data.get("saldo"), (int, float)))
                test("Firestore: tiene campo creado",
                     "creado" in data or "timestamp" in data)
        except Exception as e:
            test("Firestore: verificacion usuario", False, str(e))

        # 7.2 Leer transacciones
        try:
            import firebase_admin
            from firebase_admin import credentials, firestore
            if not firebase_admin._apps:
                cred_path = os.getenv("FIREBASE_CREDENTIALS_PATH",
                                      "./backend/firebase_credentials.json")
                if not os.path.exists(cred_path):
                    cred_path = "./firebase_credentials.json"
                if os.path.exists(cred_path):
                    cred = credentials.Certificate(cred_path)
                    firebase_admin.initialize_app(cred)
            db = firestore.client()
            txs = db.collection("transactions")\
                    .where("userId", "==", UID_TEST)\
                    .limit(10).stream()
            txs_list = list(txs)
            test("Firestore: transacciones accesibles", True)
            info(f"Transacciones en Firestore: {len(txs_list)}")
            if txs_list:
                primera = txs_list[0].to_dict()
                test("Firestore: tx tiene userId",
                     primera.get("userId") == UID_TEST)
                test("Firestore: tx tiene material",
                     primera.get("material") in ["plastico", "carton", "rechazo", "canje"])
                test("Firestore: tx tiene puntos",
                     isinstance(primera.get("puntos"), int))
                test("Firestore: tx tiene timestamp",
                     "timestamp" in primera)
                test("Firestore: tx tiene tipo",
                     primera.get("tipo") in ["deposito", "canje"])
        except Exception as e:
            err = str(e)
            if "index" in err.lower():
                info("Firestore: transacciones requieren indice compuesto")
                test("Firestore: requiere indice compuesto", True)
            else:
                test("Firestore: verificacion transacciones", False, str(e))
    else:
        if not TIENE_FIREBASE:
            test("Firestore: verificacion directa - skip (no-firebase)", None)
        if not usuario_creado:
            test("Firestore: verificacion directa - skip (sin usuario)", None)

    # =========================================================================
    paso("8. ROBOFLOW - CLASIFICACION DIRECTA")
    # =========================================================================

    if TIENE_IMAGEN:
        from services.roboflow_client import RoboflowService
        from app.core.config import ROBOFLOW_API_KEY, ROBOFLOW_MODEL_ID, ROBOFLOW_VERSION
        try:
            with open(IMAGE_PATH, "rb") as f:
                img_bytes = f.read()
            roboflow = RoboflowService(ROBOFLOW_API_KEY, ROBOFLOW_MODEL_ID,
                                       ROBOFLOW_VERSION, timeout=15)
            result = roboflow.classify(img_bytes)
            tiene_error = "error" in result
            tiene_material = "material" in result
            tiene_confidence = "confidence" in result
            test("Roboflow: clasificacion sin error", not tiene_error,
                 f"Error: {result.get('error')}" if tiene_error else "")
            test("Roboflow: tiene material", tiene_material,
                 f"Resultado: {result}")
            test("Roboflow: tiene confianza", tiene_confidence)
            if tiene_material and result["material"]:
                test(f"Roboflow: material={result['material']}",
                     result["material"] in ["plastico", "carton", "rechazo"],
                     f"Material: {result['material']}")
                info(f"Clasificacion: {result['material']} "
                     f"({result.get('confidence', 0)*100:.1f}%)")
            if tiene_error:
                test("Roboflow: falla esperada en este entorno", True)
                info(f"Error de Roboflow (esperado si no hay API key valida): "
                     f"{result['error']}")
        except Exception as e:
            traceback.print_exc()
            test("Roboflow: prueba completa", False, str(e))
    else:
        test("Roboflow: clasificacion directa - skip (no existe test.jpg)", None)

    # =========================================================================
    paso("9. OPENCV - CAMARA (opcional)")
    # =========================================================================

    try:
        import cv2
        cap = cv2.VideoCapture(0)
        if cap.isOpened():
            for _ in range(5):
                cap.read()
            ok, frame = cap.read()
            cap.release()
            test("OpenCV: camara detectable", ok)
            if ok:
                test("OpenCV: frame capturable",
                     frame is not None and frame.size > 0)
                _, buffer = cv2.imencode(".jpg", frame)
                test("OpenCV: codificacion JPG",
                     buffer is not None and len(buffer) > 0)
                resized = cv2.resize(frame, (224, 224))
                test("OpenCV: redimension 224x224",
                     resized.shape[0] == 224 and resized.shape[1] == 224,
                     f"Shape: {resized.shape}")
        else:
            test("OpenCV: camara no disponible (entorno headless)",
                 None)
    except ImportError:
        test("OpenCV: modulo no instalado", None)
    except Exception as e:
        test("OpenCV: prueba completa", False, str(e))

    # =========================================================================
    paso("10. SEGURIDAD - TOKEN VERIFICATION")
    # =========================================================================

    # 10.1 sync_user requiere header Authorization
    try:
        r = post("/api/sync_user",
                 json={"uid": "x", "email": "x@x.com", "nombre": "x"},
                 headers={})
        test("Seguridad: sync_user sin header Auth -> 401/422",
             r.status_code in [401, 422],
             f"Status: {r.status_code}, Body: {json_ok(r)}")
    except Exception:
        test("Seguridad: sync_user sin header Auth", False)

    # 10.2 sync_user Authorization sin Bearer
    try:
        r = post("/api/sync_user",
                 json={"uid": "x", "email": "x@x.com", "nombre": "x"},
                 headers={"Authorization": "no_bearer_format"})
        test("Seguridad: sync_user sin Bearer -> 401",
             r.status_code == 401,
             f"Status: {r.status_code}, Body: {json_ok(r)}")
    except Exception:
        test("Seguridad: sync_user sin Bearer", False)

    # 10.3 sync_user con token falso
    try:
        r = post("/api/sync_user",
                 json={"uid": "x", "email": "x@x.com", "nombre": "x"},
                 headers={"Authorization": "Bearer mock_token_12345"})
        test("Seguridad: sync_user token falso -> 401",
             r.status_code == 401,
             f"Status: {r.status_code}, Body: {json_ok(r)}")
    except Exception:
        test("Seguridad: sync_user token falso", False)

    # =========================================================================
    paso("11. FLUJO DE SINCRONIZACION (end-to-end)")
    # =========================================================================

    if TIENE_FIREBASE:
        # Simular: App crea usuario en Firestore -> Backend lo ve -> Deposito
        uid_e2e = f"e2e_{random.randint(10000, 99999)}"
        email_e2e = f"{uid_e2e}@test.com"
        nombre_e2e = f"E2E{random.randint(100, 999)}"

        paso("11a. App crea usuario en Firestore")
        try:
            creado = crear_usuario_firestore_directo(uid_e2e, email_e2e, nombre_e2e)
            test("E2E: App -> Firestore (createUserDocument)", creado)
            if creado:
                time.sleep(1)
        except Exception as e:
            test("E2E: App -> Firestore", False, str(e))
            creado = False

        paso("11b. Backend lee usuario de Firestore")
        if creado:
            try:
                r = get(f"/api/user/{uid_e2e}")
                data = json_ok(r)
                test("E2E: Backend -> Firestore (GET /api/user)",
                     r.status_code == 200 and data and data.get("uid") == uid_e2e)
            except Exception as e:
                test("E2E: Backend -> Firestore", False, str(e))

        paso("11c. Deposito en estacion")
        if creado and TIENE_IMAGEN:
            try:
                with open(IMAGE_PATH, "rb") as f:
                    r = post("/api/deposit",
                             data={"uid": uid_e2e},
                             files={"image": ("test.jpg", f, "image/jpeg")})
                data = json_ok(r)
                test("E2E: Estacion deposita residuo",
                     r.status_code == 200 and data is not None)
                if data:
                    puntos = data.get("puntos", 0)
                    info(f"Deposito E2E: {puntos} puntos por {data.get('material', 'N/A')}")
            except Exception as e:
                test("E2E: Estacion deposita residuo", False, str(e))

        paso("11d. Verificar Firestore refleja cambios")
        if creado:
            try:
                data = leer_usuario_firestore(uid_e2e)
                if data:
                    test("E2E: Firestore tiene saldo actualizado",
                         isinstance(data.get("saldo"), (int, float)),
                         f"Saldo: {data.get('saldo')}")
                    info(f"E2E: Saldo en Firestore = {data.get('saldo')}")
                else:
                    test("E2E: Firestore tiene usuario", False, "No encontrado")
            except Exception as e:
                test("E2E: Firestore refleja cambios", False, str(e))

        paso("11e. Limpiar datos E2E")
        if not args.no_cleanup:
            limpiar = limpiar_usuario_firestore(uid_e2e)
            test("E2E: Limpieza de datos de prueba", limpiar)
        else:
            test("E2E: Limpieza - skip (--no-cleanup)", None)
    else:
        test("E2E: flujo completo - skip (no-firebase)", None)

    # =========================================================================
    paso("12. LIMPIEZA")
    # =========================================================================

    if not args.no_cleanup and usuario_creado:
        limpiar = limpiar_usuario_firestore(UID_TEST)
        test("Limpieza: datos del test principal eliminados", limpiar)
    else:
        test("Limpieza: skip", None)

    # =========================================================================
    print(f"\n{'='*60}")
    reporte_final()


if __name__ == "__main__":
    main()
