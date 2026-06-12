# Requerimientos - EcoPuntos Inteligentes MVP

## Requerimientos Funcionales

| ID | Requerimiento | Estado |
|----|--------------|--------|
| RF-01 | El sistema debe permitir registrar usuarios via API REST | Implementado |
| RF-02 | El sistema debe generar un codigo unico de 4 caracteres alfanumericos por usuario | Implementado |
| RF-03 | El sistema debe validar el codigo de usuario contra Firestore | Implementado |
| RF-04 | El PC-Client debe capturar imagenes desde una camara web | Implementado |
| RF-05 | El sistema debe clasificar residuos usando Roboflow AI (plastico, carton, rechazo) | Implementado |
| RF-06 | El sistema debe asignar 1 punto solo si material es plastico/carton con confianza >= 0.70 | Implementado |
| RF-07 | El sistema debe registrar transacciones atomicamente en Firestore | Implementado |
| RF-08 | El sistema debe permitir canje de 5 puntos por un cupon | Implementado |
| RF-09 | La app movil debe mostrar saldo en tiempo real (polling cada 3s) | Implementado |
| RF-10 | El sistema debe ser tolerante a fallos de red/Roboflow | Implementado |

## Requerimientos No Funcionales

| ID | Requerimiento | Estado |
|----|--------------|--------|
| RNF-01 | Backend en FastAPI (Python 3.10+) | Implementado |
| RNF-02 | PC-Client en Flask + OpenCV | Implementado |
| RNF-03 | App movil en Kotlin/Jetpack Compose (SDK min 26) | Existente |
| RNF-04 | Base de datos: Firebase Firestore | Implementado |
| RNF-05 | Clasificacion: Roboflow API | Implementado |
| RNF-06 | Timeout de Roboflow: 10s maximo | Implementado |
| RNF-07 | Atomicidad en transacciones: batch + Increment | Implementado |
| RNF-08 | Sin bloqueo por hot-reload de Firebase (Singleton) | Implementado |
| RNF-09 | Las credenciales no deben estar en el repositorio | Implementado |
