# Analiza el siguiente texto noticioso y responde en formato JSON evaluando los siguientes aspectos:
#1. **Sesgo ideológico**: Detecta si el texto presenta una inclinación política o ideológica hacia alguna de las partes involucradas. Evalúa el nivel de sesgo en una escala de 1 (muy bajo) a 5 (muy alto). Agrega una breve justificación.
#2. **Uso de estereotipos**: Indica si el texto usa generalizaciones, frases estigmatizantes o simplificaciones que puedan reforzar estereotipos. Evalúa en una escala de 1 a 5. Justifica brevemente.

from config import settings
from datetime import datetime
import chromadb
import requests
from langchain.agents import AgentType, Tool, initialize_agent
from langchain.chat_models import ChatOpenAI
from langchain.embeddings import OpenAIEmbeddings
from langchain.memory import ConversationBufferWindowMemory
from langchain.prompts import PromptTemplate
from langchain.schema import HumanMessage
from langchain.chains import LLMChain
from fastapi.responses import JSONResponse
from PIL import Image
from IPython.display import display
import json
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from transformers import pipeline
import spacy
from collections import Counter 

from pysentimiento import create_analyzer

# Inicializar cliente con persistencia
client = chromadb.PersistentClient(path="./chroma_db")  
doc_collection = client.get_or_create_collection("prototipoDB")
num_docs = doc_collection.count()
print(f"Documentos en la colección: {num_docs}")
embeddings = OpenAIEmbeddings(openai_api_key=settings.API_GPT)


def analisis_profundo(text):
    # https://github.com/pysentimiento/pysentimiento
    # hate -> x.probas
    # emotion -> y.probas
    # irony -> z.probas
    hate_speech_analyzer = create_analyzer(task="hate_speech", lang="es")
    emotion_analyzer = create_analyzer(task="emotion", lang="es")
    irony_analyzer = create_analyzer(task="irony", lang="es")
    x = hate_speech_analyzer.predict(text)
    y = emotion_analyzer.predict(text)
    z = irony_analyzer.predict(text)

    resultado = {
    "hate_speech": x.probas,
    "emotion": y.probas,
    "irony": z.probas
    }

    return resultado



def analisis_sentimiento(text):
    model_name = "finiteautomata/beto-sentiment-analysis"
    model = AutoModelForSequenceClassification.from_pretrained(model_name)
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    sentiment_pipeline = pipeline("sentiment-analysis", model=model, tokenizer=tokenizer)
    nlp = spacy.load("es_core_news_sm")
    doc = nlp(text)
    frases = [sent.text.strip() for sent in doc.sents] #division en frases
    res = []
    id = 1
    for oracion in frases: # Calculo de sentimiento por cada oracion
        x = sentiment_pipeline(oracion)[0]
        res.append({
            "oracion": id,
            "label": x['label'],
            "score": x['score']
        })
        id += 1

    labels = [r["label"] for r in res] # calculo de totales
    conteo = Counter(labels)
    total = len(res)
    
    proporcion = {
        "NEG": conteo.get("NEG", 0) / total,
        "POS": conteo.get("POS", 0) / total,
        "NEU": conteo.get("NEU", 0) / total
    }
    num_polarizadas = len([r for r in res if r["label"] in ("POS", "NEG")]) # frases polarizadas (un solo sentimiento)
    polarizacion = num_polarizadas / len(res) # proporcion
    sentimiento_dominante = conteo.most_common(1)[0][0] # que predomina más

    resultado = {
        "proporcion_sentimientos": proporcion,
        "indice_polarizacion": polarizacion, # pendiente de como mostrar
        "sentimiento_dominante": sentimiento_dominante # pendiente de como mostrar
    }

    return resultado


# Función para búsqueda en Wikipedia (funciona!)
def wikipedia_search(query):
    response = requests.get(f"https://es.wikipedia.org/w/api.php", params={
        "action": "query",
        "format": "json",
        "titles": query,
        "prop": "extracts",
        "exintro": True
    })
    pages = response.json().get('query', {}).get('pages', {})
    page = next(iter(pages.values()), {})
    extract = page.get('extract', "No se encontró información en Wikipedia.")
    
    # Cortar el texto
    if extract != "No se encontró información en Wikipedia.":
        tercio_len = len(extract) // 3 
        extract = extract[:tercio_len]  # Recorte del texto para no ocupar mucho
    
    return extract

def buscar_y_mostrar_imagen(nombre_persona, nombre_archivo="imagen_resultado.jpg"):
    api_key = settings.API_GOOGLE
    search_engine_id = settings.ID_GOOGLE
    url = "https://www.googleapis.com/customsearch/v1"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36"
    }

    params = {
        "key": api_key,
        "cx": search_engine_id,
        "q": nombre_persona,
        "searchType": "image",
        "num": 1,
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        results = response.json()
        if "items" in results and len(results["items"]) > 0:
            url_imagen = results["items"][0]["link"]
            
            img_response = requests.get(url_imagen, stream=True, headers=headers)
            img_response.raise_for_status()
            
            with open(nombre_archivo, "wb") as f:
                f.write(img_response.content)
            
            imagen = Image.open(nombre_archivo)
            print("link foto")
            print(url_imagen)
            return f"Imagen encontrada en la URL: {url_imagen}"
        else:
            return "No se encontraron imágenes para la consulta."
    
    except Exception as e:
        return f"Error: {str(e)}"


def buscar_por_embeddings(pregunta):
    pregunta_embedding = embeddings.embed_query(pregunta)
    resultados = doc_collection.query(
        query_embeddings=[pregunta_embedding],
        n_results=2
    )

    docs = resultados.get("documents", [[]])[0]
    metas = resultados.get("metadatas", [[]])[0]

    if not docs:
        return "No se encontraron noticias similares."

    r = ""
    for i in range(len(docs)):
        titulo = metas[i].get("title", "Sin título")
        fecha = metas[i].get("date", "Sin fecha")
        link = metas[i].get("link", "Sin enlace")
        texto = docs[i]
        # no se le pasa el texto al modelo (no se si la contextualizacion valga y consume mucho texto)
        r += f"Noticia {i+1}: {titulo} | {fecha} | {link} \n"

    return r

# Crear las herramientas
tools = [
    Tool(
        name="buscar_por_embeddings",
        func=buscar_por_embeddings,
        description="""
            Busca documentos relevantes en ChromaDB utilizando embeddings calculados de la pregunta.
            Cuando llames a esta herramienta el Action Input es solo el texto de la pregunta en string.
        """
    ),
    Tool(
        name="Wikipedia Search",
        func=wikipedia_search,
        description="""
            Consulta Wikipedia para obtener un resumen sobre el tema.
            Si lo que buscarás es a una persona el action input es de la foma: Nombre_Apellido
        """
    ),
    Tool(
        name = "buscar_y_mostrar_imagen",
        func=buscar_y_mostrar_imagen,
        description="""Busca y reporta el url de una imagen relacioanada al action input.
        el action input debe ser un string.
        """
    ),
        Tool(
        name = "analisis profundo",
        func=analisis_profundo,
        description="""entrega un analisis del odio, la emoción y la ironia.
        """
    ),
        Tool(
        name = "analisis del sentimiento",
        func=analisis_sentimiento,
        description="""entrega la proporcion de sentimientos, indice de polarizacion y el sentimiento dominante.
        """
    )
]

# ¿Como mejorar el template para que el modelo no sea tan impredecible?
prompt_template = """
Eres un agente de inteligencia artificial que responde en español. El usuario te entregará una noticia. Tu tarea es analizarla utilizando las herramientas disponibles y construir una respuesta en **formato JSON completo y válido**.

### Flujo de trabajo obligatorio:
1. Lee y comprende la noticia entregada.
2. Extrae los actores principales (máximo 3 personas individuales, no organizaciones), además su postura frente a la noticia (Positiva, Negativa o Neutra)
3. Usa las herramientas disponibles en el siguiente orden:
   - Para cada actor:
     - Usa `Wikipedia Search` para obtener su perfil.
     - Usa `buscar_y_mostrar_magen` para encontrar su foto.
   - Aplica `analisis profundo` para obtener:
     - hate_speech
     - emotion
     - irony
   - Aplica `analisis del sentimiento` para obtener:
     - proporcion_sentimientos
     - indice_polarizacion
     - sentimiento_dominante
   - Usa `buscar_por_embeddings` para encontrar hasta 3 noticias similares.

4. **Antes de construir el JSON final, revisa si todos los datos han sido recolectados.**

5. **Importante:**
   - Si no encuentras información para un campo, deja el valor como `""`.
   - Asegúrate que no haya datos repetidos.
   - Asegúrate de cerrar correctamente todos los corchetes `{}` y llaves `[]`.
   - No repitas bloques como emociones o noticias similares.
   - No agregues texto fuera del JSON.
   - Siempre mantén los valores numéricos como **decimales** (por ejemplo: 0.15).
   - No transformes ni conviertas unidades numéricas.

### Herramientas disponibles:
- `Wikipedia Search`
- `buscar_y_mostrar_magen`
- `analisis profundo`
- `analisis del sentimiento`
- `buscar_por_embeddings`

### Formato de respuesta final:
{
  "titular": "Título de la noticia principal",
  "actores_principales": [
    {
      "nombre": "Nombre completo",
      "foto_url": "URL de imagen",
      "postura": "Postura frente al hecho",
      "perfil": "Rol o profesión"
    }
  ],
  "analisis_critico": {
    "analisis_sentimiento": {
      "proporcion_sentimientos": {
        "NEU": "valor en porcentaje",
        "NEG": "valor en porcentaje",
        "POS": "valor en porcentaje"
      },
      "indice_polarizacion": valor_numérico,
      "sentimiento_dominante": "valor textual"
    },
    "analisis_profundo": {
      "hate_speech": {
        "hateful": valor_numérico,
        "targeted": valor_numérico,
        "aggressive": valor_numérico
      },
      "emotion": {
        "others": valor_numérico,
        "joy": valor_numérico,
        "sadness": valor_numérico,
        "anger": valor_numérico,
        "surprise": valor_numérico,
        "disgust": valor_numérico,
        "fear": valor_numérico
      },
      "irony": {
        "not ironic": valor_numérico,
        "ironic": valor_numérico
      }
    }
  },
  "noticias_similares": [
    {
      "titular": "Título de noticia similar",
      "enlace": "URL de la noticia"
    }
  ]
}

"""


# ¿ se puede ajustar algo aqui para mejorar el modelo?
llm = ChatOpenAI(temperature=0.7, openai_api_key=settings.API_GPT)
prompt = PromptTemplate(input_variables=["query"], template=prompt_template)
memory = ConversationBufferWindowMemory(k=5)
agent = initialize_agent(
    tools=tools,
    llm=llm,
    agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    memory = memory,
    handle_parsing_errors = True,
    verbose=True
)

def getResponse(query):
    response = agent.run(prompt_template + "Noticia del usuario: " + query)
    try:
        parsed = json.loads(response) 
        return JSONResponse(content=parsed)
    except json.JSONDecodeError as e:
        return JSONResponse(
            status_code=500,
            content={"error": "Respuesta del modelo no es JSON válido", "detalle": str(e)}
        )
