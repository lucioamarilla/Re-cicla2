from pydantic import BaseModel
from typing import Optional


class SyncUserRequest(BaseModel):
    uid: str
    email: str
    nombre: str


class SyncUserResponse(BaseModel):
    uid: str
    email: str
    nombre: str
    codigo: str = ""
    saldo: int = 0


class UserResponse(BaseModel):
    uid: str
    email: str
    nombre: str
    codigo: str = ""
    saldo: int


class DepositResponse(BaseModel):
    success: bool
    userId: str
    material: str
    confianza: float
    puntos: int
    nuevoSaldo: int
    mensaje: str


class RedeemRequest(BaseModel):
    uid: str
    puntos: int = 5


class RedeemResponse(BaseModel):
    success: bool
    nuevo_saldo: int
    cupon: str


class TransactionResponse(BaseModel):
    id: str
    userId: str
    nombre: str
    material: str
    puntos: int
    confidence: float
    timestamp: str
    tipo: str


class TransactionListResponse(BaseModel):
    transactions: list[TransactionResponse]
