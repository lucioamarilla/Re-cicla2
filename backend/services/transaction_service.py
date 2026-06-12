import random
import string
from firebase_admin import firestore


def _generar_codigo():
    chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    sufijo = "".join(random.choices(chars, k=6))
    return f"ECO-{sufijo}"


class TransactionService:
    def __init__(self):
        from app.core.firebase import get_db
        self.db = get_db()

    def get_user(self, uid: str):
        if self.db is None:
            return None
        doc = self.db.collection("users").document(uid).get()
        if not doc.exists:
            return None
        data = doc.to_dict()
        return {
            "uid": uid,
            "email": data.get("email", ""),
            "nombre": data.get("nombre", ""),
            "codigo": data.get("codigo", ""),
            "saldo": data.get("saldo", 0),
        }

    def get_user_by_code(self, codigo: str):
        if self.db is None:
            return None
        users = (
            self.db.collection("users")
            .where("codigo", "==", codigo)
            .limit(1)
            .stream()
        )
        for user in users:
            data = user.to_dict()
            return {
                "uid": data.get("uid", ""),
                "email": data.get("email", ""),
                "nombre": data.get("nombre", ""),
                "codigo": data.get("codigo", ""),
                "saldo": data.get("saldo", 0),
            }
        return None

    def create_user(self, uid: str, email: str, nombre: str):
        if self.db is None:
            return {"uid": uid, "email": email, "nombre": nombre, "codigo": "", "saldo": 0}
        doc_ref = self.db.collection("users").document(uid)
        if doc_ref.get().exists:
            return self.get_user(uid)
        codigo = _generar_codigo()
        doc_ref.set({
            "uid": uid,
            "codigo": codigo,
            "email": email,
            "nombre": nombre,
            "saldo": 0,
            "creado": firestore.SERVER_TIMESTAMP,
        })
        return {"uid": uid, "email": email, "nombre": nombre, "codigo": codigo, "saldo": 0}

    def process_deposit(self, uid: str, material: str, confidence: float, threshold: float):
        if self.db is None:
            return {"puntos": 0, "nuevoSaldo": 0}
        puntos = 1
        user_ref = self.db.collection("users").document(uid)
        tx_ref = self.db.collection("transactions").document()
        user_doc = user_ref.get()
        nombre = user_doc.to_dict().get("nombre", uid) if user_doc.exists else uid
        batch = self.db.batch()
        batch.update(user_ref, {"saldo": firestore.Increment(puntos)})
        batch.set(tx_ref, {
            "userId": uid,
            "nombre": nombre,
            "material": material,
            "puntos": puntos,
            "confidence": confidence,
            "timestamp": firestore.SERVER_TIMESTAMP,
            "tipo": "deposito",
        })
        batch.commit()
        saldo_actual = (user_ref.get().to_dict() or {}).get("saldo", 0)
        return {"puntos": puntos, "nuevoSaldo": saldo_actual}

    def get_transactions(self, uid: str, limit: int = 20):
        if self.db is None:
            return []
        try:
            docs = (
                self.db.collection("transactions")
                .where("userId", "==", uid)
                .order_by("timestamp", direction="DESCENDING")
                .limit(limit)
                .stream()
            )
            return [{"id": d.id, **d.to_dict()} for d in docs]
        except Exception as e:
            err = str(e)
            if "index" in err.lower():
                print(f"Firestore requiere índice compuesto. Mensaje: {err[:200]}")
                return []
            raise

    def redeem_points(self, uid: str, puntos: int = 5):
        if self.db is None:
            return {"error": "Firestore no disponible"}
        user_ref = self.db.collection("users").document(uid)
        user_doc = user_ref.get()
        if not user_doc.exists:
            return {"error": "Usuario no encontrado"}
        saldo = user_doc.to_dict().get("saldo", 0)
        if saldo < puntos:
            return {"error": f"Saldo insuficiente. Necesitas {puntos}, tienes {saldo}"}
        batch = self.db.batch()
        batch.update(user_ref, {"saldo": firestore.Increment(-puntos)})
        tx_ref = self.db.collection("transactions").document()
        batch.set(tx_ref, {
            "userId": uid,
            "nombre": user_doc.to_dict().get("nombre", ""),
            "material": "canje",
            "puntos": -puntos,
            "confidence": 1.0,
            "timestamp": firestore.SERVER_TIMESTAMP,
            "tipo": "canje",
        })
        batch.commit()
        nuevo_saldo = user_ref.get().to_dict().get("saldo", 0)
        return {"success": True, "nuevo_saldo": nuevo_saldo, "cupon": "Cafe gratis en la estacion EcoPuntos"}
