from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from config import settings
from langchain_utils import getResponse  
import json

class TextRequest(BaseModel):
    text: str

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
    user_text = req.text
    print(f"Texto recibido: {user_text}")
    print("\n  -------- \n")
    # Llamamos la función de LangChain
    #analysis_result = getResponse(user_text)
    #print(analysis_result)
    analysis_result = """{
  "titular": "Israel ampliará su ofensiva 'a la mayor parte de Gaza'",
  "actores_principales": [
    {
      "nombre": "Israel Katz",
      "foto_url": "https://upload.wikimedia.org/wikipedia/commons/a/af/Israel_Katz_on_July_3%2C_2024_%28cropped%29.jpg",
      "postura": "El ministro israelí de Defensa, Israel Katz, anunció la ampliación de la ofensiva y emitió una orden de evacuación para los residentes de Jan Yunis en Gaza.",
      "perfil": "Ministro de Defensa de Israel, miembro de la Knéset por el Likud."
    },
    {
      "nombre": "Leo rodriguez",
      "foto_url": "https://cdn-icons-png.flaticon.com/512/6840/6840478.png",
      "postura": "desarrollar armando este proyecto para su tesis.",
      "perfil": "developer"
    }
  ],
  "analisis_critico": {
    "sesgo": "Posible sesgo político y de poder en favor de Israel debido a la falta de información de la perspectiva palestina.",
    "lenguaje_cargado": "El lenguaje utilizado por Israel Katz es directo y enfocado en la acción militar.",
    "propaganda": "No se puede determinar con certeza si hay propaganda en la noticia dada la información limitada.",
    "faltante_informacion": "Falta información sobre la perspectiva palestina y posibles consecuencias humanitarias."
  },
  "noticias_similares": [
    {
      "titular": "Nuevos ataques israelíes en Gaza causan decenas de muertos y heridos",
      "resumen": "Al menos 46 palestinos murieron y decenas resultaron heridos en ataques israelíes contra la Franja de Gaza.",
      "enlace": "https://noticia1.com"
    },
    {
      "titular": "Continúan agresiones israelíes en territorios ocupados",
      "resumen": "Se reportan más de 50,000 muertos y 115,338 heridos en Gaza desde el inicio de las agresiones israelíes en octubre de 2023.",
      "enlace": "https://noticia2.com"
    }
  ]
}"""
    parsed_result = json.loads(analysis_result)
    return parsed_result
    #return analysis_result


