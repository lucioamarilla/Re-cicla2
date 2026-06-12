from fastapi import APIRouter, Depends, HTTPException
from app.schemas.schemas import SyncUserRequest, SyncUserResponse, UserResponse
from app.core.auth import verify_token

router = APIRouter(prefix="/api", tags=["auth"])


@router.get("/user/{uid}", response_model=UserResponse)
async def get_user(uid: str):
    uid = uid.strip()
    if not uid:
        raise HTTPException(400, "UID inválido")
    from services.transaction_service import TransactionService
    svc = TransactionService()
    user = svc.get_user(uid)
    if not user:
        raise HTTPException(404, "Usuario no encontrado")
    return UserResponse(**user)


@router.get("/user/code/{codigo}", response_model=UserResponse)
async def get_user_by_code(codigo: str):
    codigo = codigo.strip().upper()
    if not codigo:
        raise HTTPException(400, "Código inválido")
    from services.transaction_service import TransactionService
    svc = TransactionService()
    user = svc.get_user_by_code(codigo)
    if not user:
        raise HTTPException(404, "Código no encontrado")
    return UserResponse(**user)


@router.post("/sync_user", response_model=SyncUserResponse)
async def sync_user(req: SyncUserRequest, token: dict = Depends(verify_token)):
    if req.uid != token.get("uid"):
        raise HTTPException(403, "El UID no coincide con el token")
    from services.transaction_service import TransactionService
    svc = TransactionService()
    result = svc.create_user(req.uid, req.email, req.nombre)
    return SyncUserResponse(**result)
