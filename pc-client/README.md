# EcoPuntos - Cliente PC

Interfaz web con camara para depositar residuos y obtener puntos.

## Requisitos

- Python 3.10+
- Camara web conectada
- Backend de EcoPuntos corriendo en `http://localhost:8000`

## Instalacion

```bash
pip install -r requirements.txt
```

## Configuracion

Editar `.env`:
```
BACKEND_URL=http://localhost:8000
CAMERA_INDEX=0
FLASK_PORT=5000
```

## Ejecucion

```bash
python app.py
```

Abrir `http://localhost:5000`

## Funcionalidades

- Validacion de codigo de usuario contra backend
- Captura de foto con OpenCV (redimensionada a 224x224)
- Envio al backend para clasificacion con IA
- Maquina de 5 estados con feedback visual (verde/rojo/naranja)
- Botones debug para pruebas sin backend
- Auto-reset a pantalla de inicio tras 5 segundos
