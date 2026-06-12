# EcoPuntos Inteligentes - MVP 

Bienvenido al repositorio del MVP de **EcoPuntos Inteligentes**, un sistema integral diseñado para clasificar residuos mediante Inteligencia Artificial y recompensar a los usuarios con puntos canjeables a través de una aplicación móvil.

## Descripción del Proyecto

Este proyecto es un Producto Mínimo Viable (MVP) que integra hardware de captura (cámara), modelos de IA locales para la clasificación de residuos (plástico, cartón, rechazo), un backend robusto para el motor transaccional y una aplicación móvil nativa para la gestión de los usuarios.

## Arquitectura y Módulos

El proyecto está dividido en cuatro componentes principales:

1. **Backend (`/backend`)**: Desarrollado en **Python con FastAPI**. Actúa como el núcleo del sistema, gestionando usuarios, transacciones, saldos de puntos y sirviendo de puente para la inferencia de la IA.
2. **Cliente PC (`/pc-client`)**: Una interfaz web minimalista servida con **Flask** que utiliza **OpenCV** para capturar imágenes desde una cámara local y enviarlas al backend.
3. **Aplicación Móvil (`/mobile-app`)**: App nativa en **Kotlin** (Android) donde los usuarios pueden generar sus códigos de sesión, revisar su historial de transacciones y canjear sus EcoPuntos.
4. **Modelo de IA (`/ia-model`)**: Contiene el modelo de Deep Learning (basado en MobileNet/TensorFlow Lite) encargado de clasificar el material reciclable.

---

## Estructura del Repositorio

```text
ecopuntos-inteligentes-mvp/
├── docs/                              # Documentación técnica y de gestión del equipo
│   ├── requerimientos.md              # Requisitos Funcionales y No Funcionales
│   ├── mvp-plan.md                    # Plan de iteraciones y cronograma del Día 1
│   ├── demo-script.md                 # Guión para la demostración final
│   └── manual-tecnico.md              # Instrucciones detalladas de instalación por rol
├── backend/                           # API Principal (FastAPI)
│   ├── app/                           # Código fuente de la API (routers, schemas, models)
│   ├── services/                      # Lógica de negocio (IA, sistema de puntos)
│   ├── requirements.txt               # Dependencias del backend
│   ├── .env.example                   # Plantilla de variables de entorno
│   └── run.py                         # Script de inicio (Uvicorn)
├── pc-client/                         # Cliente local con cámara (Flask + OpenCV)
│   ├── app.py                         # Servidor Flask e interfaz web
│   ├── camera.py                      # Módulo de captura de video
│   ├── static/                        # Archivos estáticos (HTML, CSS, JS)
│   ├── requirements.txt               # Dependencias del cliente
│   ├── .env.example                   # Plantilla de variables de entorno (URL del backend)
│   └── README.md                      # Instrucciones específicas del cliente PC
├── mobile-app/                        # Aplicación Android Nativa (Kotlin)
│   ├── app/src/main/java/...          # Código fuente (Activities, Retrofit API)
│   ├── build.gradle                   # Configuración de Gradle
│   └── README.md                      # Instrucciones para Android Studio
├── ia-model/                          # Modelos de Machine Learning
│   ├── model.tflite                   # Modelo preentrenado exportado
│   ├── labels.txt                     # Etiquetas de clasificación
│   └── training/                      # Scripts opcionales para fine-tuning
├── scripts/                           # Utilidades de desarrollo
│   ├── setup_db.py                    # Script para inicializar tablas
│   └── seed_data.py                   # Script para poblar datos de prueba
├── .gitignore                         # Archivos ignorados por Git
└── README.md                          # Este archivo