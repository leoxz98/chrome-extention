# bug al cargar el historial del chat desde chrome storage <- 
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from config import settings
from langchain_utils import getResponse  
import json
import os
from openai import OpenAI
from config import settings

client = OpenAI(api_key=settings.API_GPT)
 

class ChatInput(BaseModel):
    message: str
    history: list  # Lista de pares (rol, contenido), para mantener contexto

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
  "resumen": "Los presidentes de Palestina, Mahmoud Abbas, y de Francia, Emmanuel Macron, reclamaron hoy un alto el fuego en Gaza y exigieron a Israel permitir la entrada de ayuda humanitaria al territorio. Macron y Abbas defendieron la implementación de la solución de dos Estados para acabar con el histórico diferendo, como exigen varias resoluciones del Consejo de Seguridad de la ONU.",  
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
    "Unsubstantiated claims bias": {
      "presente": false,
      "porque": []
    },
    "Opinion statements presented as facts": {
      "presente": false,
      "porque": []
    },
    "Sensationalism or Emotionalism": {
      "presente": false,
      "porque": []
    },
    "Ad Hominem or Mudslinging": {
      "presente": true,
      "porque": [
        "Se menciona un ataque de Netanyahu y su hijo Yair contra Macron, lo cual podría considerarse un ataque personal."
      ]
    },
    "Mind reading": {
      "presente": false,
      "porque": []
    },
    "Slant bias": {
      "presente": false,
      "porque": []
    },
    "Subjective qualifying adjectives": {
      "presente": false,
      "porque": []
    },
    "Bias by labeling and word choice": {
      "presente": false,
      "porque": []
    },
    "Flawed logic": {
      "presente": false,
      "porque": []
    }
  },
  "actores_principales": [
    {
      "nombre": "Mahmoud Abbas",
      "foto_url": "https://upload.wikimedia.org/wikipedia/commons/6/6f/Mahmoud_Abbas_2024.jpg",
      "postura": "Reclama un alto el fuego en Gaza y exige a Israel permitir la entrada de ayuda humanitaria al territorio.",      
      "perfil": "Mahmoud Abbas es un político palestino que se desempeña como presidente de Palestina desde 2005. Es miembro de Fatah y ha sido un defensor de la solución de dos Estados para el conflicto israelí-palestino."
    },
    {
      "nombre": "Emmanuel Macron",
      "foto_url": "https://upload.wikimedia.org/wikipedia/commons/3/3d/Emmanuel_Macron_February_2025.jpg",
      "postura": "Defiende la creación de un Estado palestino, idea que rechaza Israel.",
      "perfil": "Emmanuel Macron es un político francés que actualmente se desempeña como presidente de Francia desde 2017. Anteriormente fue ministro de Economía, Industria y Asuntos Digitales en el gobierno de François Hollande."
    }
  ],
  "proporcion_sentimientos": {
    "NEG": 0.3333333333333333,
    "POS": 0.3333333333333333,
    "NEU": 0.3333333333333333
  },
  "indice_polarizacion": 0.55555555555
}"""
    return r
    #return json.loads(result)

@app.post("/chat")
async def chat(input: ChatInput):
    # Empieza el contexto con un mensaje de sistema si quieres dar instrucciones
    messages = [{"role": "system", "content": "Eres un asistente útil que responde preguntas sobre noticias."}]
    
    # Agrega el historial del usuario
    messages += [
    {"role": role, "content": content}
    for role, content in input.history
    if isinstance(content, str) and isinstance(role, str)
]

    
    # Agrega el nuevo mensaje del usuario
    messages.append({"role": "user", "content": input.message})

    
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages,
        temperature=0.7
    )

    reply = response.choices[0].message.content
    return {"reply": reply}