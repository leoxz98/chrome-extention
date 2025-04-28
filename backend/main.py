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
    r = getResponse(user_text)

    result = {
  "titular": "Netanyahu aseguró que Israel trabaja en un acuerdo para liberar a diez de los rehenes de Hamas en Gaza (EFE/ARCHIVO)",
  "actores_principales": [
    {
      "nombre": "Benjamin Netanyahu",
      "foto_url": "https://encrypted-tbn2.gstatic.com/images?q=tbn:ANd9GcQnMVOeWCJQV5i2WYXFo4v1-itSFGW00dsY8THM_qVbnLE2U2PH",
      "postura": "buena",
      "perfil": "Político, Primer Ministro de Israel"
    },
    {
      "nombre": "Eitan Mor",
      "foto_url": "https://maozisrael.org/wp-content/webp-express/webp-images/uploads/2024/02/eitanMor.jpg.webp",
      "postura": "victima",
      "perfil": "Guardia de seguridad en el festival de música Nova"
    },
    {
      "nombre": "Tzvika Mor",
      "foto_url": "https://static-cdn.toi-media.com/www/uploads/2024/05/Tzvika-Mor-TOI.jpg",
      "postura": "Neutral",
      "perfil": "Fundador del Foro Tikva"
    }
  ],
  "analisis_critico": {
    "analisis_sentimiento": {
      "proporcion_sentimientos": {
        "NEU": 0.3,
        "NEG": 0.5,
        "POS": 0.2
      },
      "indice_polarizacion": 0.75,
      "sentimiento_dominante": "NEG"
    },
    "analisis_profundo": {
      "hate_speech": {
        "hateful": 0.25,
        "targeted": 0.15,
        "aggressive": 0.1
      },
      "emotion": {
        "others": 0.1,
        "joy": 0.05,
        "sadness": 0.2,
        "anger": 0.3,
        "surprise": 0.1,
        "disgust": 0.15,
        "fear": 0.1
      },
      "irony": {
        "not ironic": 0.7,
        "ironic": 0.3
      }
    }
  },
  "noticias_similares": [
    {
      "titular": "Israel: Oficiales de la Fuerza Armada exigen finalizar combates en la Franja de Gaza",
      "enlace": "https://www.telesurtv.net/israel-oficiales-fuerza-armada-exigen/"}
      ]
  }
  

    print(type(r))
    #print(result)
    print("aqui")
    print(r)
    return r
    #return analysis_result


