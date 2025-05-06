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
    #print(type(r))
    print("aqui")

    result = """{
  "titular": "Abbas y Macron exigen fin de la guerra y ayuda para Gaza",
  "resumen": "Los presidentes de Palestina, Mahmoud Abbas, y de Francia, Emmanuel Macron, reclamaron un alto el fuego en Gaza y la entrada de ayuda humanitaria. Macron y Abbas defienden la solución de dos Estados para el conflicto. Netanyahu criticó a Macron por su apoyo a la creación de un Estado palestino.",
  "noticias_similares": [
    {
      "titular": "Trump dice que hay 'progresos' en las negociaciones entre Israel y Hamás para un alto el fuego",
      "enlace": "https://www.diarioestrategia.cl/texto-diario/mostrar/5252680/trump-dice-hay-progresos-negociaciones-entre-israel-hamas-alto-fuego"
    },
    {
      "titular": "Reacciones en Francia ante eventual reconocimiento de Palestina",
      "enlace": "https://www.prensa-latina.cu/2025/04/10/reacciones-en-francia-ante-eventual-reconocimiento-de-palestina/"
    }
  ],
  "sesgos": {
    "opiniones_como_hechos": {
      "presente": false,
      "ejemplos": []
    },
    "sensacionalismo_emocionalismo": {
      "presente": false,
      "ejemplos": []
    },
    "lectura_de_mente": {
      "presente": true,
      "ejemplos": [
        "'Coincidieron en que la Autoridad Nacional Palestina debe asumir la responsabilidad en ese territorio'"
      ]
    }
  },
  "actores_principales": [
    {
      "nombre": "Mahmoud Abbas",
      "foto_url": "https://upload.wikimedia.org/wikipedia/commons/6/6f/Mahmoud_Abbas_2024.jpg",
      "postura": "Reclama un alto el fuego en Gaza y exige a Israel permitir la entrada de ayuda humanitaria al territorio.",
      "perfil": "Mahmoud Abbas es un político palestino que actualmente se desempeña como presidente de Palestina desde el 15 de enero de 2005."
    },
    {
      "nombre": "Emmanuel Macron",
      "foto_url": "https://upload.wikimedia.org/wikipedia/commons/3/3d/Emmanuel_Macron_February_2025.jpg",
      "postura": "Defiende la implementación de la solución de dos Estados para acabar con el histórico diferendo.",
      "perfil": "Emmanuel Macron es un economista y político francés, vigesimoquinto presidente de la República Francesa desde 2017."
    },
    {
      "nombre": "Benjamín Netanyahu",
      "foto_url": "https://upload.wikimedia.org/wikipedia/commons/7/74/Benjamin_Netanyahu%2C_February_2023.jpg",
      "postura": "Rechaza la creación de un Estado palestino y cualquier plan para desplazar por la fuerza a los habitantes del enclave costero.",
      "perfil": "Benjamín Netanyahu es un político israelí que actualmente se desempeña como primer ministro de Israel desde diciembre de 2022."
    }
  ],
  "proporcion_sentimientos": {
    "NEG": 0.16666666666666666,
    "POS": 0.0,
    "NEU": 0.8333333333333334
  },
  "indice_polarizacion": 0.16666666666666666
}"""
    return r
    #return json.loads(result)


