from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from config import settings  # Importamos la configuración

# Definimos un modelo Pydantic para validar y deserializar el JSON entrante
class TextRequest(BaseModel):
    text: str

app = FastAPI()

# Configurar CORS para permitir solicitudes desde el frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, restringe esto a los dominios específicos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    print(f"Server running on port: {settings.PORT}")
    return {'message': 'API is running', 'status': 'ok'}

@app.post("/analyze")
async def analyze(req: TextRequest):
    # Ahora podemos acceder al campo 'text' directamente
    user_text = req.text
    print(f"Texto recibido: {user_text}")
    
    # Aquí puedes implementar tu lógica de análisis
    response = f"Texto analizado: '{user_text}'"
    
    return {"result": response}

