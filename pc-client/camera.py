import os
import cv2
import base64
from dotenv import load_dotenv

load_dotenv()

CAMERA_INDEX = int(os.getenv("CAMERA_INDEX", "0"))


class Camera:
    def __init__(self):
        self.cap = None

    def init(self):
        if self.cap is not None and self.cap.isOpened():
            return
        self.cap = cv2.VideoCapture(CAMERA_INDEX)
        if not self.cap.isOpened():
            raise RuntimeError(f"No se pudo abrir la camara indice {CAMERA_INDEX}")

    def capture_base64(self):
        self.init()
        for _ in range(5):
            self.cap.read()
        ok, frame = self.cap.read()
        if not ok:
            raise RuntimeError("No se pudo capturar el frame")
        resized = cv2.resize(frame, (224, 224))
        ok, buffer = cv2.imencode(".jpg", resized)
        if not ok:
            raise RuntimeError("No se pudo codificar la imagen")
        return base64.b64encode(buffer).decode("utf-8")

    def get_frame_jpeg(self):
        self.init()
        ok, frame = self.cap.read()
        if not ok:
            return None
        ok, buffer = cv2.imencode(".jpg", frame)
        if not ok:
            return None
        return buffer.tobytes()

    def release(self):
        if self.cap is not None:
            self.cap.release()
            self.cap = None


camera = Camera()
