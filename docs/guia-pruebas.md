# Guia de Pruebas - EcoPuntos Inteligentes MVP

## Pruebas de Humo (Smoke Tests)

### Verificacion de Firebase

1. Ir a Firebase Console > Firestore Database
2. Crear coleccion `users`
3. Crear documento con ID `A3F2`:
   ```json
   {
     "nombre": "Usuario Test",
     "saldo": 0,
     "creado": (timestamp)
   }
   ```
4. Verificar desde el backend: `curl http://localhost:8000/api/user/A3F2`

### Verificacion de Roboflow (aislada)

```bash
./scripts/test_roboflow.sh test.jpg
```

Debe retornar JSON con `predictions` o `top` y `confidence`.

### Verificacion de Hardware (OpenCV)

```bash
python scripts/test_camera.py
```

Debe generar `test_camera.jpg` sin errores.

## Casos de Prueba End-to-End

### CP-01: Deposito Exitoso (Happy Path)

**Pasos:**
1. Registrar usuario via API: `POST /api/register` con nombre "Lucio"
2. Anotar el codigo generado (ej: `A3F2`)
3. Abrir `http://localhost:5000`
4. Ingresar el codigo y presionar "Validar"
5. Colocar una botella PET clara frente a la camara
6. Presionar "Tomar foto"

**Resultado esperado:**
- Frontend se pinta de verde
- Mensaje: "Aprobado! +1 Punto"
- En Firestore: `users/A3F2.saldo` incrementa en 1
- Nueva transaccion en `transactions` con `material: "plastico"`, `puntos: 1`

### CP-02: Deposito Fallido por Material Incorrecto

**Pasos:**
1. Validar codigo valido en PC-client
2. Colocar basura organica (resto de comida, servilleta sucia) frente a la camara
3. Presionar "Tomar foto"

**Resultado esperado:**
- Frontend se pinta de rojo
- Mensaje: "Residuo rechazado o no reconocido"
- En Firestore: saldo no cambia
- Transaccion registrada con `puntos: 0`, `material: "rechazo"`

### CP-03: Deposito Fallido por Baja Confianza

**Pasos:**
1. Validar codigo valido en PC-client
2. Colocar un objeto borroso o mal iluminado (ej: carton arrugado con poca luz)
3. Presionar "Tomar foto"

**Resultado esperado:**
- La IA puede detectar "carton" pero con confidence < 0.70
- Regla de negocio bloquea el punto
- Frontend rojo, 0 puntos, saldo inalterado

### CP-04: Resiliencia ante Caida de IA (Prueba de Caos)

**Pasos:**
1. Desconectar internet de la PC
2. O cambiar `ROBOFLOW_API_KEY` por una falsa en `backend/.env`
3. Reiniciar backend
4. Intentar un deposito en PC-client

**Resultado esperado:**
- Sin crash ni trace de error en consola
- Frontend muestra fondo naranja/rojo
- Mensaje: "Servicio de IA temporalmente no disponible"
- Backend continua vivo esperando al siguiente usuario
- En Firestore: no se crea transaccion (no se contacto Roboflow)

### CP-05: Validacion de Atomicidad (Estrés)

**Pasos:**
1. Registrar usuario (saldo inicial 0)
2. Enviar dos peticiones `POST /api/deposit` simultaneas (con codigo y foto)
3. Verificar saldo final

**Resultado esperado:**
- `firestore.Increment()` protege contra race conditions
- Si ambos depositos son exitosos, saldo = 2 (no 1)
- No hay perdida de datos aunque las peticiones lleguen en el mismo milisegundo

## Tabla de Troubleshooting

| Problema | Diagnostico | Solucion |
|----------|-------------|----------|
| Firebase 403 Permission Denied | serviceAccountKey.json incorrecto o reglas de Firestore restrictivas | Verificar el archivo de credenciales. Reglas recomendadas: `match /users/{userId} { allow read, write: if request.auth != null && request.auth.uid == userId; }` |
| OpenCV Error: Assertion failed (!empty()) | Camara ocupada por otra app o indice incorrecto | Cerrar Zoom, OBS, etc. Probar CAMERA_INDEX=1 en `.env` |
| Roboflow KeyError: 'predictions' | Umbral muy alto o plan gratuito excedido | Bajar threshold en Roboflow. Verificar limite de requests mensuales (plan Starter: 1000/mes) |
| FastAPI CORS Error | Cliente no autorizado | Verificar `allow_origins=["*"]` en CORSMiddleware |
| Firebase: "The default Firebase app already exists" | Hot-reload de Uvicorn | El Singleton en `firebase.py` lo resuelve. Si persiste, usar `reload=False` en run.py |
| Timeout en Roboflow (>10s) | Red lenta o servidor congestionado | Aumentar timeout en `RoboflowService` o reintentar |
| "Codigo no encontrado" en PC-client | Usuario no registrado o codigo incorrecto | Registrar via `POST /api/register` o crear manualmente en Firebase Console |

## Checklist de Verificacion

- [ ] Backend arranca con `python backend/run.py`
- [ ] `curl http://localhost:8000/health` responde `{"status":"ok"}`
- [ ] Registro de usuario funciona
- [ ] Validacion de codigo funciona
- [ ] PC-client arranca con `python pc-client/app.py`
- [ ] Interfaz web carga en `http://localhost:5000`
- [ ] Camara captura imagen correctamente
- [ ] Flujo completo: validar -> capturar -> clasificar -> resultado
- [ ] Mocks de debug funcionan (sin backend)
- [ ] Sin secretos en el repositorio
- [ ] App Android compila y se conecta al backend
