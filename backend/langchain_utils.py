# Analiza el siguiente texto noticioso y responde en formato JSON evaluando los siguientes aspectos:
#0 resumen (highlights)
#1. **Sesgo ideológico**: Detecta si el texto presenta una inclinación política o ideológica hacia alguna de las partes involucradas. Evalúa el nivel de sesgo en una escala de 1 (muy bajo) a 5 (muy alto). Agrega una breve justificación.
#2. **Uso de estereotipos**: Indica si el texto usa generalizaciones, frases estigmatizantes o simplificaciones que puedan reforzar estereotipos. Evalúa en una escala de 1 a 5. Justifica brevemente.
# se pueden agregar nuevos documentos a la revisión ya hecha?
# como empezar a redactar el sgte avance (que cap, que contenido)?
# un solo indicador y el resto texto
# sintesis visual global
# equibilibrio del texto 
# sintesis
# 1 resumen
# 2 analisis del sesgo (indicador visual y en resumen escrito)
# 3 actores y reseña
# 4 articulos similares


# circular: {'proporcion_sentimientos': {'NEG': 0.16666666666666666, 'POS': 0.0, 'NEU': 0.8333333333333334}
# barra 'indice_polarizacion': 0.16666666666666666, color indicando 
# resto gpt

# tesis (documento)
# 1 arquitectura de software y desarrollo(arquitectura -quienes son los usuarios- casos de uso - componentes - despliegue) (diagrama caso de uso y componenetes)
# dentro de los componentes (mockup y diseño del reporte)
# funcionamiento del agente (langchain - tools - prompt template)
# 2 resultados (prueba del software, metricas , tablas , etc....) 
# 3 pruebas de usuario (ellos eliguen las noticias)
# (resumen del analisis critico ¿que info mostrar?)
# pruebas (diseño y resultados) # definir metricas, tablas 

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
from collections import defaultdict
from pysentimiento import create_analyzer

# Inicializar cliente con persistencia
client = chromadb.PersistentClient(path="./chroma_db")  
doc_collection = client.get_or_create_collection("prototipoDB")
num_docs = doc_collection.count()
print(f"Documentos en la colección: {num_docs}")
embeddings = OpenAIEmbeddings(openai_api_key=settings.API_GPT)


def analisis_profundo(text):
    nlp = spacy.load("es_core_news_sm")
    hate_speech_analyzer = create_analyzer(task="hate_speech", lang="es")

    doc = nlp(text)
    frases = [sent.text.strip() for sent in doc.sents]

    suma_hateful = 0.0
    suma_targeted = 0.0
    suma_aggressive = 0.0
    resultados = []

    for i, frase in enumerate(frases, 1):
        x = hate_speech_analyzer.predict(frase)
        probas = x.probas
        resultados.append({
            "oracion": i,
            "texto": frase,
            "probas": probas
        })
        suma_hateful += probas.get("hateful", 0)
        suma_targeted += probas.get("targeted", 0)
        suma_aggressive += probas.get("aggressive", 0)

    total = len(frases)
    promedio = {
        "odio": suma_hateful / total,
        "odio dirigido": suma_targeted / total,
        "tono agresivo": suma_aggressive / total
    }

    return promedio


from transformers import AutoModelForSequenceClassification, AutoTokenizer, pipeline
import spacy
from collections import Counter

def analisis_sentimiento(text):
    # https://help.sesamm.com/article/32-sentiment-polarity
    model_name = "finiteautomata/beto-sentiment-analysis"
    model = AutoModelForSequenceClassification.from_pretrained(model_name)
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    sentiment_pipeline = pipeline("sentiment-analysis", model=model, tokenizer=tokenizer)

    nlp = spacy.load("es_core_news_sm")
    doc = nlp(text)
    frases = [sent.text.strip() for sent in doc.sents]

    res = []
    id = 1
    for oracion in frases:
        x = sentiment_pipeline(oracion)[0]
        res.append({
            "oracion": id,
            "label": x['label'],
            "score": x['score']
        })
        id += 1

    labels = [r["label"] for r in res]
    conteo = Counter(labels)
    total = len(res)

    proporcion = {
        "NEG": conteo.get("NEG", 0) / total,
        "POS": conteo.get("POS", 0) / total,
        "NEU": conteo.get("NEU", 0) / total
    }

    # Polaridad general del artículo
    pos = proporcion["POS"]
    neg = proporcion["NEG"]
    polaridad = (pos - neg) / (pos + neg + 1e-6)  # evitar división por cero

    resultado = {
        "proporcion_sentimientos": proporcion,
        "indice_polarizacion": polaridad  # polaridad según la fórmula (-1 a 1)
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
tools_a = [
    Tool(
        name="buscar_por_embeddings",
        func=buscar_por_embeddings,
        description="""
            Busca documentos relevantes en ChromaDB utilizando embeddings calculados de la pregunta.
            Cuando llames a esta herramienta el Action Input es solo el texto de la pregunta en string.
        """
    )
]

tools_b = [
    Tool(
        name = "analisis_sentimiento",
        func=analisis_sentimiento,
        description="""entrega la proporcion de sentimientos, indice de polarizacion y el sentimiento dominante.
        """
    )
]

tools_c = [
    Tool(
        name="wikipedia_search",
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
    )
]

# 
prompt_template_a = """Eres un asistente especializado en análisis de noticias. A partir del texto que se te proporciona, debes extraer la siguiente información en formato JSON:

1. "titular": una frase corta que represente el título de la noticia.
2. "resumen": una síntesis clara y concisa de los hechos más importantes, usando un máximo de 5 líneas.
3. "noticias_similares": una lista de noticias relacionadas obtenidas mediante búsqueda por embeddings. Cada elemento debe contener:
   - "titular": el título de la noticia similar.
   - "enlace": la URL donde se puede consultar.

Para obtener las noticias similares, utiliza la herramienta `buscar_por_embeddings` con el texto completo como entrada. El resultado debe integrarse en el campo "noticias_similares".

Responde exclusivamente en formato JSON con las claves "titular", "resumen" y "noticias_similares".

IMPORTANTE: No debes inventar las noticias similares ni usar tu conocimiento previo para generarlas. Estas deben provenir únicamente de la herramienta `buscar_por_embeddings`.

Ejemplo de salida esperada:
{
  "titular": "Terremoto de magnitud 7,2 sacude el norte de Chile",
  "resumen": "Un sismo de gran magnitud se registró esta madrugada en la zona norte del país, provocando daños menores y cortes de energía. No se reportan víctimas fatales. Las autoridades monitorean posibles réplicas. El SHOA descartó riesgo de tsunami. La ONEMI activó protocolos de emergencia.",
  "noticias_similares": [
    {
      "titular": "Fuerte sismo afecta región de Antofagasta sin dejar víctimas",
      "enlace": "https://ejemplo.com/noticia1"
    },
    {
      "titular": "ONEMI activa protocolos tras sismo en el norte",
      "enlace": "https://ejemplo.com/noticia2"
    }
  ]
}
"""

# Analisis del sesgo
prompt_template_b = """Eres un asistente experto en análisis crítico de noticias en español. Sigue los pasos estrictamente para entregar el análisis solicitado, en el formato requerido.

PASO 1: Lee cuidadosamente el texto de la noticia entregado por el usuario.

PASO 2: Analiza la noticia en busca de los siguientes sesgos discursivos:
- Unsubstantiated claims bias
- Opinion statements presented as facts
- Sensationalism or Emotionalism
- Ad Hominem or Mudslinging
- Mind reading
- Slant bias
- Subjective qualifying adjectives
- Bias by labeling and word choice
- Flawed logic

Para cada tipo de sesgo, indica si está presente (`true` o `false`) y proporciona un porqué de su presencia en la noticia si corresponde, además no debe ser como mucho 3 lineas de texto de largo.

PASO 3: Devuelve ÚNICAMENTE un objeto JSON con la siguiente estructura, sin ninguna explicación adicional:

```json
{
  "sesgos": {
    "Sesgo A": {
      "presente": true,
      "porque": ["..."]
    },
    "Sesgo B": {
      "presente": false,
      "porque": []
    },
    "Sesgo C": {
      "presente": true,
      "porque": ["..."]
    }
  }
}

 """

# Actores 
prompt_template_c = """Eres un analista experto en noticias. Tu tarea es identificar hasta 3 actores principales (personas) mencionados en la siguiente noticia. Para cada uno, debes:

1. Indicar su nombre completo.
2. Determinar su postura frente al hecho (a favor o en contra, y por qué) en un máximo de 2 líneas. Usa únicamente el contenido de la noticia para esta parte.
3. Buscar el URL de una imagen representativa usando la herramienta `buscar_y_mostrar_imagen` (el input debe ser su nombre completo como string).
4. Consultar su perfil profesional en Wikipedia usando la herramienta `wikipedia_search`, también con su nombre completo en formato Nombre_Apellido.

**Tu respuesta debe ser exclusivamente en formato JSON**, con la siguiente estructura:

{
  "actores_principales": [
    {
      "nombre": "Nombre completo",
      "foto_url": "URL de imagen",
      "postura": "Postura frente al hecho",
      "perfil": "Rol o profesión o descripción breve según Wikipedia"
    },
    ...
  ]
}

Instrucciones importantes:
- Solo incluye personas. No incluyas organizaciones, instituciones ni entidades colectivas.
- Si hay menos de 3 personas relevantes, incluye solo las que correspondan.
- No utilices ninguna herramienta que no sea `buscar_y_mostrar_imagen` o `wikipedia_search`, y solo para los campos indicados.
- **No agregues explicaciones fuera del JSON.**

"""


# Configuración del modelo
llm = ChatOpenAI(temperature=0.7, openai_api_key=settings.API_GPT)


# Memorias independientes por agente
memory_a = ConversationBufferWindowMemory(k=5)
memory_b = ConversationBufferWindowMemory(k=5)
memory_c = ConversationBufferWindowMemory(k=5)

# Agente A con herramientas de embeddings
agent_a = initialize_agent(
    tools=tools_a,
    llm=llm,
    agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    memory=memory_a,
    handle_parsing_errors=True,
    verbose=True
)

# Agente B con herramientas de análisis
agent_b = initialize_agent(
    tools=tools_b,
    llm=llm,
    agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    memory=memory_b,
    handle_parsing_errors=True,
    verbose=True
)

# Agente C con herramientas de búsqueda en Wikipedia e imágenes
agent_c = initialize_agent(
    tools=tools_c,
    llm=llm,
    agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    memory=memory_c,
    handle_parsing_errors=True,
    verbose=True
)



def getResponse(query):
    response_a = agent_a.run(prompt_template_a + "Noticia del usuario: " + query)
    print("paso 1")
    response_b = llm.predict(prompt_template_b + query)
    print("paso 2")
    response_c = agent_c.run(prompt_template_c + "Noticia del usuario: " + query)
    print("paso 3")
    response_d = analisis_sentimiento(query)
    print("paso 4")

    try:
        # Convertir todos los strings JSON a diccionarios Python
        parsed_a = json.loads(response_a)
        parsed_b = json.loads(response_b)
        parsed_c = json.loads(response_c)
        parsed_d = response_d if isinstance(response_d, dict) else json.loads(response_d)

        # Unir todos los diccionarios en uno solo (plano)
        combined = {**parsed_a, **parsed_b, **parsed_c, **parsed_d}
        print(json.dumps(combined, indent=2, ensure_ascii=False))
        return JSONResponse(content=combined)

    except json.JSONDecodeError as e:
        return JSONResponse(
            status_code=500,
            content={
                "error": "Alguna respuesta no es JSON válido",
                "detalle": str(e)
            }
        )

