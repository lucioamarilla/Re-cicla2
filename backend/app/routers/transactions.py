from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from app.core.config import ROBOFLOW_API_KEY, ROBOFLOW_MODEL_ID, ROBOFLOW_VERSION, CONFIDENCE_THRESHOLD

router = APIRouter(prefix="/api", tags=["transactions"])


@router.post("/deposit")
async def deposit(uid: str = Form(...), image: UploadFile = File(...)):
    from services.transaction_service import TransactionService
    from services.roboflow_client import RoboflowService

    roboflow = RoboflowService(ROBOFLOW_API_KEY, ROBOFLOW_MODEL_ID, ROBOFLOW_VERSION)

    uid = uid.strip()
    if not uid:
        raise HTTPException(400, "UID inválido")

    svc = TransactionService()
    user = svc.get_user(uid)
    if not user:
        raise HTTPException(404, "Usuario no encontrado")

    contents = await image.read()
    if len(contents) > 5 * 1024 * 1024:
        raise HTTPException(400, "La imagen no puede superar 5MB")

    result = roboflow.classify(contents)
    if "error" in result:
        return {
            "success": False,
            "userId": uid,
            "material": "rechazo",
            "confianza": 0.0,
            "puntos": 0,
            "nuevoSaldo": user["saldo"],
            "mensaje": "Servicio de IA temporalmente no disponible",
            "error": result["error"],
        }

    material = result["material"]
    confianza = result["confidence"]
    tx_result = svc.process_deposit(uid, material, confianza, CONFIDENCE_THRESHOLD)

    return {
        "success": tx_result["puntos"] > 0,
        "userId": uid,
        "material": material,
        "confianza": confianza,
        "puntos": tx_result["puntos"],
        "nuevoSaldo": tx_result["nuevoSaldo"],
        "mensaje": "¡Aprobado! +1 Punto" if tx_result["puntos"] > 0 else "Residuo rechazado o no reconocido",
    }


@router.get("/transactions/{uid}")
async def get_transactions(uid: str, limit: int = 20):
    from services.transaction_service import TransactionService
    svc = TransactionService()
    return svc.get_transactions(uid.strip(), min(limit, 50))


@router.post("/redeem")
async def redeem(uid: str = Form(...), puntos: int = Form(5)):
    uid = uid.strip()
    if not uid:
        raise HTTPException(400, "UID inválido")
    from services.transaction_service import TransactionService
    svc = TransactionService()
    result = svc.redeem_points(uid, puntos)
    if "error" in result:
        raise HTTPException(400, result["error"])
    return result
