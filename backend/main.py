# bug al borrar algo y darle cuanto esta vacio y despues darle a copiar
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from config import settings
from langchain_utils import getResponse  
import json
import os
from openai import OpenAI
from config import settings

client = OpenAI(api_key=settings.API_GPT) # archivo .env
 

class ChatInput(BaseModel):
    """
    Define el esquema de entrada para la solicitud de chat.

    Attributes:
        message (str): El mensaje actual del usuario.
        history (List[Tuple[str, str]]): Historial de la conversación como una lista
                                         de tuplas (rol, contenido del mensaje).
    """
    message: str
    history: list  

class TextRequest(BaseModel):
    """
    Define el esquema de entrada para la solicitud de análisis de texto.
    Attributes: 
      text (str): El texto del artículo de noticias a ser analizado.
    """
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
    """
    Gestiona las solicitudes para realizar un análisis crítico de un texto de noticias.

    Recibe el texto del usuario, lo pasa a un agente de LangChain (definido en `langchain_utils.py`),
    y devuelve el resultado del análisis. Este endpoint es el punto de entrada para
    procesar el contenido del artículo de noticias.

    Args:
        req (TextRequest): Un objeto que contiene el texto del artículo de noticias
                           que se desea analizar.

    Returns:
        dict: Un diccionario que contiene el resultado del análisis proporcionado
              por el agente de LangChain.

    Raises:
        HTTPException: Puede lanzar una excepción si el procesamiento en `getResponse` falla
                       o si hay un error de validación del esquema de entrada.
    """
    user_text = req.text
    print(f"Texto recibido: {user_text}")
    print("\n  -------- \n")
    r = getResponse(user_text) # agente de langchain en langchain_utils.py
    return r
    

@app.post("/chat")
async def chat(input: ChatInput):
    """
    Gestiona las solicitudes de chat para interactuar con un modelo de lenguaje.

    Construye el contexto de la conversación incluyendo un mensaje de sistema,
    el historial de la conversación del usuario y el mensaje actual.
    Luego, envía esta secuencia de mensajes a un modelo de lenguaje (ej. GPT-3.5-turbo)
    y devuelve la respuesta generada.

    Args:
        input (ChatInput): Un objeto que contiene el mensaje actual del usuario
                           y el historial de la conversación.

    Returns:
        dict: Un diccionario que contiene la respuesta del modelo bajo la clave "reply".
              Ejemplo: {"reply": "¡Hola! ¿En qué puedo ayudarte hoy?"}

    Raises:
        HTTPException: Puede lanzar una excepción si la comunicación con la API
                       del modelo de lenguaje falla o si hay un error de validación
                       (gestionado por FastAPI/Pydantic implícitamente).
    """
    
    # Inicializa la lista de mensajes con un rol de sistema para establecer el comportamiento del LLM.
    # Esto le indica al modelo cómo debe actuar (e.g., "Eres un asistente útil...").
    messages = [{"role": "system", "content": "Eres un asistente útil que responde preguntas sobre noticias."}]
    messages += [
    {"role": role, "content": content}
    for role, content in input.history
    if isinstance(content, str) and isinstance(role, str)
]
    # Agrega el mensaje actual del usuario al final del contexto de la conversación.
    messages.append({"role": "user", "content": input.message})

    # Realiza la llamada a la API del modelo de lenguaje.
    # 'model': Especifica el modelo a utilizar (ej. "gpt-3.5-turbo").
    # 'messages': La secuencia completa de la conversación (sistema, historial, usuario).
    # 'temperature': Controla la aleatoriedad de la respuesta del modelo (0.7 es un valor común
    #                para respuestas equilibradas, no demasiado creativas ni demasiado predecibles).  
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages,
        temperature=0.7
    )

    # Extrae el contenido de la respuesta del modelo.
    # Se asume que la respuesta exitosa tendrá al menos una elección.
    reply = response.choices[0].message.content

     # Devuelve la respuesta del modelo al cliente.
    return {"reply": reply}