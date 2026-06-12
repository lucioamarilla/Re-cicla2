# MVP Plan - EcoPuntos Inteligentes

## Dia 1 (Implementacion)

### Manana
- [x] Analisis de codigo existente (ramas Re-cicla2 + rama_leo)
- [x] Creacion de estructura de directorios
- [x] Implementacion del backend FastAPI (core, servicios, routers)
- [x] Implementacion del PC-Client Flask + OpenCV
- [x] Implementacion de frontend con maquina de 5 estados

### Tarde
- [x] Pruebas de integracion automatizadas
- [x] Correccion de bugs (CORS, transacciones, circular imports)
- [x] Creacion de documentacion y guia de pruebas
- [x] Verificacion final (21/24 tests pasados, 3 skip por falta de imagen)

## Pendientes
- [ ] Crear indice compuesto en Firestore (transactions.userId + transactions.timestamp DESC)
- [ ] Probar flujo completo con imagen real (test.jpg)
- [ ] Compilar y probar app movil contra backend
