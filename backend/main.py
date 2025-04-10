from fastapi import FastAPI
from config import settings  # Importamos la configuración



app = FastAPI()

@app.get("/")
def read_root():
    print(f"test: {settings.PORT}")
    return {'hola': 'mundo'}
