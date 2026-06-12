# EcoPuntos Inteligentes - MVP

Sistema integral de reciclaje inteligente con IA. Clasifica residuos mediante vision computacional (Roboflow) y recompensa a los usuarios con puntos canjeables.

## Arquitectura

- **`backend/`**: API REST en FastAPI (Python 3.10+). Orquestador central: Firebase Firestore, Roboflow AI, logica de negocio.
- **`pc-client/`**: Interfaz web con camara (Flask + OpenCV). Captura imagenes y se comunica con el backend.
- **`mobile-app/`**: App Android nativa en Kotlin/Jetpack Compose. Gestion de usuarios, historial y canje de puntos.

## Inicio Rapido

```bash
# Backend
cd backend
pip install -r requirements.txt
python run.py

# PC-Client (otra terminal)
cd pc-client
pip install -r requirements.txt
python app.py
```

Abrir `http://localhost:5000` para la interfaz de deposito.

## Requisitos

- Python 3.10+
- Camara web
- Cuenta Firebase (plan Spark)
- Cuenta Roboflow (plan Starter)

## Bugs Resueltos en esta Integracion

| Bug | Solucion |
|-----|----------|
| Firebase crash en hot-reload | Singleton con `firebase_admin._apps` |
| Race condition en saldo | `firestore.Increment()` en vez de read+write |
| Falta de atomicidad | `batch.commit()` para operaciones de doble escritura |
| Roboflow sin tolerancia a fallos | Timeout 10s, manejo granular de excepciones |
| UI sin feedback visual | Maquina de 5 estados con colores de fondo y auto-reset |
| Sin degradacion graceful | Modo debug sin Firebase |
