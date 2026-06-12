from fastapi import Header, HTTPException
from firebase_admin import auth as firebase_auth


def verify_token(authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token inválido")
    token = authorization.split("Bearer ")[1]
    try:
        decoded = firebase_auth.verify_id_token(token)
        return decoded
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Token inválido: {str(e)}")


def optional_user(authorization: str | None = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization.split("Bearer ")[1]
    try:
        return firebase_auth.verify_id_token(token)
    except Exception:
        return None
