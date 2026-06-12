# Manual Tecnico - EcoPuntos Inteligentes MVP

## Requisitos del Sistema

- Python 3.10 o superior
- Camara web (USB o integrada)
- Android Studio (para la app movil, opcional)
- Cuenta en Firebase (plan Spark)
- Cuenta en Roboflow (plan Starter)

## Instalacion

### 1. Backend (FastAPI)

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Configurar `backend/.env` con las credenciales reales:
- `FIREBASE_CREDENTIALS_PATH`: ruta al archivo JSON de service account de Firebase
- `ROBOFLOW_API_KEY`: API key de Roboflow
- `ROBOFLOW_MODEL_ID`: ID del modelo en Roboflow
- `ROBOFLOW_VERSION`: version del modelo

Colocar el archivo `firebase_credentials.json` (o `serviceAccountKey.json`) en `backend/`.

Ejecutar:
```bash
python run.py
```

El servidor arrancara en `http://localhost:8000`.

### 2. PC-Client (Flask + OpenCV)

```bash
cd pc-client
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Configurar `pc-client/.env`:
- `BACKEND_URL`: URL del backend (default: `http://localhost:8000`)
- `CAMERA_INDEX`: indice de la camara (default: `0`)
- `FLASK_PORT`: puerto del servidor (default: `5000`)

Ejecutar:
```bash
python app.py
```

Abrir en el navegador: `http://localhost:5000`

### 3. App Movil (Android/Kotlin)

Abrir `mobile-app/` en Android Studio.
Sincronizar Gradle y ejecutar en dispositivo o emulador.
La app ya esta configurada con Firebase (google-services.json incluido).

## Arquitectura

```
ecopuntos-inteligentes-mvp/
backend/       # FastAPI - Logica de negocio, Firebase, Roboflow
pc-client/     # Flask + OpenCV - Interfaz de usuario y captura de camara
mobile-app/    # Kotlin/Android - App movil para usuarios
```

### Flujo de datos

1. Usuario ingresa codigo en PC-client
2. PC-client valida contra backend (`GET /api/user/{code}`)
3. Si es valido, usuario presiona "Tomar foto"
4. PC-client captura imagen de la camara (redimensionada a 224x224)
5. PC-client envia imagen al backend (`POST /api/deposit`)
6. Backend clasifica con Roboflow
7. Backend aplica regla de negocio (plastico/carton + confianza >= 0.70 = 1 punto)
8. Backend escribe en Firestore atomicamente (Increment + batch)
9. Resultado se muestra en pantalla (verde = exito, rojo = rechazo)

## Endpoints de la API

| Metodo | Ruta | Descripcion |
|--------|------|-------------|
| GET | `/health` | Health check |
| POST | `/api/register` | Registrar nuevo usuario |
| GET | `/api/user/{code}` | Obtener datos de usuario |
| POST | `/api/deposit` | Procesar deposito (imagen + codigo) |
| GET | `/api/transactions/{userId}` | Historial de transacciones |
| POST | `/api/redeem` | Canjear puntos |

## Pruebas Rapidas

### Probar Roboflow independientemente

```bash
curl -X POST "https://detect.roboflow.com/residuos-reciclaje/1?api_key=9bV8sIpOxb79beiXxskn" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    --data-urlencode "image@test.jpg"
```

### Probar camara con script minimo

```bash
python scripts/test_camera.py
```

### Probar backend

```bash
# Health check
curl http://localhost:8000/health

# Registrar usuario
curl -X POST http://localhost:8000/api/register \
    -H "Content-Type: application/json" \
    -d '{"nombre":"Test"}'

# Obtener usuario
curl http://localhost:8000/api/user/XXXX
```
