import os
import firebase_admin
from firebase_admin import credentials, firestore

_db = None

def get_db():
    global _db
    if _db is not None:
        return _db
    if firebase_admin._apps:
        _db = firestore.client()
        return _db
    cred_path = os.getenv("FIREBASE_CREDENTIALS_PATH", "./firebase_credentials.json")
    if not os.path.exists(cred_path):
        print("Firebase credentials not found. Running without persistence.")
        _db = None
        return None
    cred = credentials.Certificate(cred_path)
    firebase_admin.initialize_app(cred)
    _db = firestore.client()
    print("Firebase initialized successfully")
    return _db
