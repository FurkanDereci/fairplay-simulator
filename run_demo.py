import uvicorn
from src.backend.app import app

if __name__ == "__main__":
    print("Starting FairPlay Simulator FastAPI Backend Server on http://0.0.0.0:8000 ...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
