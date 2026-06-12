#!/bin/bash
# run_tests.sh - Pruebas rapidas del sistema EcoPuntos
# Uso:
#   1. Activar venv: source ecopuntos-venv/bin/activate
#   2. Iniciar backend: cd backend && python run.py &
#   3. Ejecutar: bash scripts/run_tests.sh
#
# Opciones:
#   --image test.jpg   Incluye prueba de deposito con imagen
#   --all              Modo completo (backend + pc-client)

SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
BACKEND_URL="${BACKEND_URL:-http://localhost:8000}"
PYTHON="${PYTHON:-python3}"

VERDE='\033[92m'; ROJO='\033[91m'; AMARILLO='\033[93m'
AZUL='\033[94m'; BOLD='\033[1m'; RESET='\033[0m'

PASADAS=0; FALLOS=0
ok()   { echo -e "  ${VERDE}[PASS]${RESET} $1"; ((PASADAS++)); }
fail() { echo -e "  ${ROJO}[FAIL]${RESET} $1"; ((FALLOS++)); }
info() { echo -e "  ${AZUL}[INFO]${RESET} $1"; }
paso() { echo -e "\n${BOLD}$1${RESET}"; }

IMAGE_PATH=""
while [[ $# -gt 0 ]]; do
    case $1 in --image) IMAGE_PATH="$2"; shift 2 ;; --all) shift ;; *) shift ;; esac
done

echo -e "${BOLD}=== ECO PUNTOS - RUNNER DE PRUEBAS ===${RESET}"
echo "Directorio: $SCRIPT_DIR"
echo "Python: $($PYTHON --version 2>&1)"

# ------------------------------------------------------------------
paso "1. DEPENDENCIES"
# ------------------------------------------------------------------
for mod in fastapi flask; do
    $PYTHON -c "import $mod" 2>/dev/null && ok "$mod instalado" || fail "$mod NO instalado"
done
$PYTHON -c "import cv2" 2>/dev/null && ok "opencv instalado" || info "opencv no instalado"
$PYTHON -c "import firebase_admin" 2>/dev/null && ok "firebase-admin instalado" || info "firebase-admin no instalado"

# ------------------------------------------------------------------
paso "2. ARCHIVOS DEL PROYECTO"
# ------------------------------------------------------------------
for f in \
    backend/run.py backend/app/__init__.py backend/app/core/config.py \
    backend/app/core/firebase.py backend/app/routers/auth.py \
    backend/app/routers/transactions.py backend/services/roboflow_client.py \
    backend/services/transaction_service.py backend/requirements.txt \
    pc-client/app.py pc-client/camera.py pc-client/templates/index.html \
    pc-client/static/css/styles.css pc-client/static/js/main.js \
    pc-client/requirements.txt .gitignore; do
    [ -f "$SCRIPT_DIR/$f" ] && ok "$f" || fail "FALTA: $f"
done

# ------------------------------------------------------------------
paso "3. SEGURIDAD"
# ------------------------------------------------------------------
[ -f "$SCRIPT_DIR/backend/.env" ] && ok "backend/.env existe" || fail "backend/.env falta"
for p in ".env" "firebase_credentials.json" "__pycache__/"; do
    grep -q "$p" "$SCRIPT_DIR/.gitignore" 2>/dev/null && ok ".gitignore ignora: $p" || fail ".gitignore NO ignora: $p"
done

# ------------------------------------------------------------------
paso "4. BACKEND HTTP"
# ------------------------------------------------------------------
if curl -sf "$BACKEND_URL/health" > /dev/null 2>&1; then
    ok "Backend OK en $BACKEND_URL"
    [ "$(curl -s "$BACKEND_URL/health")" = '{"status":"ok"}' ] && ok "Health endpoint OK" || fail "Health endpoint falla"
    
    CODE=$(curl -s -o /dev/null -w "%{http_code}" "$BACKEND_URL/api/user/TEST")
    ok "GET /api/user/TEST -> $CODE"
    
    CORS=$(curl -s -D - -o /dev/null -H "Origin: http://localhost:5000" "$BACKEND_URL/health" 2>&1 | grep -ci "access-control-allow-origin")
    [ "$CORS" -gt 0 ] && ok "CORS headers OK" || fail "CORS headers faltan"
    
    TX=$(curl -s -o /dev/null -w "%{http_code}" "$BACKEND_URL/api/transactions/TEST")
    ok "GET /api/transactions/TEST -> $TX"
else
    fail "Backend NO disponible en $BACKEND_URL"
    info "Ejecuta: cd backend && python run.py &"
fi

# ------------------------------------------------------------------
paso "5. TEST PYTHON DE INTEGRACION (v1 - sistema con codigos)"
# ------------------------------------------------------------------
CMD="$PYTHON $SCRIPT_DIR/scripts/test_integration.py --backend-url $BACKEND_URL"
[ -n "$IMAGE_PATH" ] && CMD="$CMD --image $IMAGE_PATH"
echo "  $CMD"
$CMD || true

# ------------------------------------------------------------------
paso "6. DEBUG COMPLETO (v2 - sistema con UIDs)"
# ------------------------------------------------------------------
CMD="$PYTHON $SCRIPT_DIR/scripts/debug_full_system.py --backend-url $BACKEND_URL"
[ -n "$IMAGE_PATH" ] && CMD="$CMD --image $IMAGE_PATH"
echo "  $CMD"
PYTHONPATH="$SCRIPT_DIR/backend:$SCRIPT_DIR" $CMD || true

# ------------------------------------------------------------------
paso "7. RESUMEN"
# ------------------------------------------------------------------
echo -e "${BOLD}Comandos utiles:${RESET}"
echo "  Backend:     cd backend && python run.py"
echo "  PC-Client:   cd pc-client && python app.py"
echo "  Tests (v1):  python scripts/test_integration.py --image test.jpg"
echo "  Tests (v2):  python scripts/debug_full_system.py --image test.jpg"
echo ""
