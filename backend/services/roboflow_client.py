import base64
import requests


class RoboflowService:
    MAPEO_CLASES = {
        "plastic": "plastico",
        "plastico": "plastico",
        "plástico": "plastico",
        "botella": "plastico",
        "pet": "plastico",
        "polietileno": "plastico",
        "cardboard": "carton",
        "carton": "carton",
        "cartón": "carton",
        "caja": "carton",
        "papel": "carton",
        "paper": "carton",
        "vidrio": "vidrio",
        "glass": "vidrio",
        "metal": "metal",
        "lata": "metal",
        "aluminio": "metal",
        "trash": "plastico",
        "basura": "plastico",
        "organico": "plastico",
        "food": "plastico",
    }

    def __init__(self, api_key, model_id, version, timeout=10):
        self.api_key = api_key
        self.model_id = model_id
        self.version = version
        self.timeout = timeout

    def classify(self, image_bytes):
        img_b64 = base64.b64encode(image_bytes).decode("utf-8")
        url = f"https://detect.roboflow.com/{self.model_id}/{self.version}"
        try:
            response = requests.post(
                url,
                params={"api_key": self.api_key},
                data=img_b64,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=self.timeout,
            )
            response.raise_for_status()
            data = response.json()
            predictions = data.get("predictions", [])
            if not predictions:
                return {"material": "plastico", "confidence": 0.01}
            top = data.get("top", "")
            if top:
                clase = top.lower()
                confidence = data.get("confidence", 0.0)
            else:
                best = max(predictions, key=lambda p: p.get("confidence", 0))
                clase = best.get("class", "").lower()
                confidence = best.get("confidence", 0.0)
            if confidence < 0.01:
                confidence = 0.01
            material = self.MAPEO_CLASES.get(clase, "plastico")
            return {"material": material, "confidence": confidence}
        except requests.exceptions.Timeout:
            return {"error": "timeout", "material": "plastico", "confidence": 0.01}
        except requests.exceptions.RequestException as e:
            return {"error": f"roboflow_api_error: {str(e)}", "material": "plastico", "confidence": 0.01}
