# Demo Script - EcoPuntos Inteligentes MVP

## Duracion: 3 minutos

### Escena 1: Registro (30s)

1. Abrir app movil (Android)
2. Ingresar nombre: "Lucio"
3. Presionar "Registrarse"
4. **Resultado**: Aparece codigo de 4 digitos (ej: A3F2) y saldo 0

### Escena 2: Deposito en PC-Client (90s)

1. Abrir navegador en `http://localhost:5000`
2. Ingresar codigo A3F2 en el campo
3. Presionar "Validar"
4. **Resultado**: Fondo verde, saludo "Bienvenido Lucio", feed de camara activo
5. Colocar botella PET frente a la camara
6. Presionar "Tomar foto"
7. **Resultado** (5s):
   - Preview de la imagen capturada
   - Spinner "IA analizando residuo..."
   - Fondo verde + "Aprobado! +1 Punto"

### Escena 3: Verificacion en App (30s)

1. En la app movil, observar saldo actualizado (debe mostrar 1 punto)
2. Ir a historial de transacciones
3. **Resultado**: Transaccion visible con material "plastico" y +1 punto

### Escena 4: Canje (30s)

1. En la app, presionar "Canjear"
2. **Resultado**: Cupon "Cafe gratis en la estacion EcoPuntos"
3. Saldo disminuye en 5 puntos
