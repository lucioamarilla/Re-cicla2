### Estructura del proyecto

ecopuntos-inteligentes-mvp/
│
├── README.md                          # Descripción general del proyecto, cómo ejecutar cada componente
├── .gitignore                         # Ignorar archivos de entorno, builds, cachés
│
├── docs/                              # Documentación del equipo
│   ├── requerimientos.md              # RF y RNF
│   ├── mvp-plan.md                    # Plan de iteraciones y cronograma del día 1
│   ├── demo-script.md                 # Guión para la demostración final
│   └── manual-tecnico.md              # Instrucciones de instalación para cada rol
│
├── backend/                           # FastAPI - Backend principal
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                    # Creación de la app FastAPI, montado de routers
│   │   ├── database.py                # Configuración de SQLAlchemy y conexión a DB (SQLite/PostgreSQL)
│   │   ├── models.py                  # Tablas: Usuario, Transaccion
│   │   ├── schemas.py                 # Pydantic models para requests/responses
│   │   ├── routers/
│   │   │   ├── usuarios.py            # POST /registro, GET /saldo, GET /transacciones
│   │   │   ├── validar.py             # POST /validar/codigo
│   │   │   ├── clasificar.py          # POST /clasificar (recibe imagen, llama a IA)
│   │   │   └── canje.py               # POST /canje
│   │   ├── services/
│   │   │   ├── ia_service.py          # Carga el modelo, clasifica imagen
│   │   │   └── puntos_service.py      # Lógica de asignación de puntos y transacciones
│   │   └── utils/
│   │       └── codigo_generator.py    # Generación de códigos únicos de 4 dígitos
│   ├── requirements.txt               # fastapi, uvicorn, sqlalchemy, tensorflow-cpu, python-multipart, etc.
│   ├── .env.example                   # Variables de entorno (DB_URL, SECRET_KEY)
│   └── run.py                         # Script para iniciar el servidor (uvicorn)
│
├── pc-client/                         # Script Python para la PC con cámara (interfaz web local)
│   ├── app.py                         # Servidor Flask que sirve la interfaz y maneja cámara
│   ├── camera.py                      # Funciones de captura con OpenCV
│   ├── static/
│   │   ├── index.html                 # Interfaz web minimalista (campo código, botón tomar foto, área mensajes)
│   │   ├── style.css                  # Estilos básicos
│   │   └── script.js                  # Llamadas a Flask (AJAX) y actualización de UI
│   ├── requirements.txt               # flask, opencv-python, requests, python-dotenv
│   ├── .env.example                   # BACKEND_URL (ej. http://localhost:8000)
│   └── README.md                      # Instrucciones para correr el cliente
│
├── mobile-app/                        # Kotlin (Android nativo)
│   ├── app/
│   │   ├── src/
│   │   │   ├── main/
│   │   │   │   ├── java/com/example/ecopuntos/
│   │   │   │   │   ├── MainActivity.kt           # Pantalla principal (código + saldo)
│   │   │   │   │   ├── HistoryActivity.kt        # Historial
│   │   │   │   │   ├── RedeemActivity.kt         # Canje
│   │   │   │   │   ├── network/
│   │   │   │   │   │   ├── ApiService.kt         # Interface Retrofit
│   │   │   │   │   │   ├── RetrofitClient.kt    # Configuración de Retrofit
│   │   │   │   │   │   └── Models.kt            # Data classes
│   │   │   │   │   ├── data/
│   │   │   │   │   │   └── SharedPrefsManager.kt
│   │   │   │   │   └── utils/
│   │   │   │   │       └── Constants.kt
│   │   │   │   └── res/                          # layouts, values, drawable
│   │   │   └── test/ y androidTest/
│   │   ├── build.gradle (app level)
│   │   └── proguard-rules.pro
│   ├── build.gradle (project level)
│   ├── settings.gradle
│   ├── gradle.properties
│   ├── local.properties.example       # ruta del SDK (opcional)
│   └── README.md                      # Instrucciones para abrir en Android Studio
│
├── ia-model/                          # Modelos preentrenados
│   ├── model.tflite                   # MobileNet adaptado (o modelo en otro formato)
│   ├── labels.txt                     # plastic, carton, rechazo
│   ├── training/                      # (opcional) scripts de fine-tuning
│   │   └── train_model.py
│   └── README.md                      # Origen del modelo, cómo reemplazarlo
│
└── scripts/                           # Utilidades comunes (opcional)
    ├── setup_db.py                    # Crear tablas en la base de datos
    └── seed_data.py                   # Datos de prueba (opcional)
