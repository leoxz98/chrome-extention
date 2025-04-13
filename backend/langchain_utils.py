from langchain.chat_models import ChatOpenAI
from langchain.schema import HumanMessage
from config import settings

""" Cosas que hacer
    - Implementar chromadb (script aparte para subir archivos)
    - implementar tool de wikipedia
    - armar prompt template
    - implementar agente con los 3 anteriores (devuelve en json)
    
"""


# Inicializamos el modelo de lenguaje
llm = ChatOpenAI(
    api_key=settings.API_GPT,
    temperature=0.7,
    model_name="gpt-3.5-turbo"
)

def analyze_text_with_langchain(text: str) -> str:
    """Resumen lo siguiente en un maximo de 5 lineas: """
    try:
        messages = [
            HumanMessage(content=f"Haz un resumen en un maximo de 5 lineas del siguiente texto: {text}")
        ]
        response = llm(messages)
        print("aqui xd: ")
        print(response.content)
        return response.content
    except Exception as e:
        return f"Error al procesar el texto: {str(e)}"
