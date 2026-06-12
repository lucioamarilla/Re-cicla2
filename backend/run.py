import uvicorn
from app.core.config import BACKEND_PORT

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=BACKEND_PORT, reload=False)
