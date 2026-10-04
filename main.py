"""
SuperFarmer Main Entrypoint
Exports the FastAPI application from app.py.
Allows standard invocation:
    uvicorn main:app --reload
    python main.py
"""
from app import app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=5000, reload=True)
