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

# https://help.sesamm.com/article/32-sentiment-polarity

def analisis_sentimiento(text):
    """
    Realiza un análisis de sentimiento a nivel de oración en un texto dado
    y calcula la proporción de sentimientos (positivo, negativo, neutro)
    y un índice de polaridad general.

    Utiliza un modelo de análisis de sentimiento pre-entrenado en español
    (finiteautomata/beto-sentiment-analysis) y Spacy para la segmentación
    de oraciones.

    Args:
        text (str): El texto de entrada (ej., un artículo de noticias) a analizar.

    Returns:
        dict: Un diccionario que contiene:
            - "proporcion_sentimientos" (dict): Un diccionario con la proporción
            de oraciones clasificadas como "NEG" (negativas), "POS" (positivas)
            y "NEU" (neutras).
            - "indice_polarizacion" (float): Un valor entre -1 y 1 que indica
            la polaridad general del texto. Un valor cercano a 1 indica una
            polaridad positiva fuerte, -1 una polaridad negativa fuerte, y 0
            una polaridad neutra o equilibrada.
    """
    # Define el nombre del modelo de Hugging Face para análisis de sentimiento en español.
    model_name = "finiteautomata/beto-sentiment-analysis"
    # Carga el modelo pre-entrenado para clasificación de secuencias.
    model = AutoModelForSequenceClassification.from_pretrained(model_name)
    # Carga el tokenizador asociado al modelo para procesar el texto.
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    # Crea un pipeline de análisis de sentimiento utilizando el modelo y el tokenizador cargados.
    # Este pipeline simplifica la aplicación del modelo a los textos.
    sentiment_pipeline = pipeline("sentiment-analysis", model=model, tokenizer=tokenizer)
    # Carga el modelo de procesamiento de lenguaje natural de Spacy para español.
    # Se utiliza para la segmentación de oraciones (dividir el texto en frases individuales).
    nlp = spacy.load("es_core_news_sm")
    # Procesa el texto de entrada con Spacy para crear un objeto 'doc'.
    doc = nlp(text)
    # Extrae cada oración del objeto 'doc' y las guarda en una lista.
    # `.sents` es un iterador de oraciones y `.text.strip()` elimina espacios en blanco.
    frases = [sent.text.strip() for sent in doc.sents]
    res = []
    id = 1
    # Itera sobre cada oración extraída para realizar el análisis de sentimiento.
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
    # Calcula la proporción de cada tipo de sentimiento sobre el total de oraciones.
    # `.get(key, 0)` asegura que si una etiqueta no existe, su conteo sea 0 para evitar errores.
    proporcion = {
        "NEG": conteo.get("NEG", 0) / total,
        "POS": conteo.get("POS", 0) / total,
        "NEU": conteo.get("NEU", 0) / total
    } 
    pos = proporcion["POS"]
    neg = proporcion["NEG"]
    
    # Calcula el índice de polaridad.
    # La fórmula (POS - NEG) / (POS + NEG) normaliza el valor entre -1 y 1.
    polaridad = (pos - neg) / (pos + neg)  

    resultado = {
        "proporcion_sentimientos": proporcion,
        "indice_polarizacion": polaridad  
    }

    return resultado



# Función para búsqueda en Wikipedia (funciona!)
def wikipedia_search(query):
    """
    Realiza una búsqueda de una consulta específica en la Wikipedia en español
    y devuelve un extracto introductorio del artículo encontrado.
    Si no se encuentra información, retorna un mensaje predefinido.
    Para evitar textos excesivamente largos, solo se devuelve el primer tercio del extracto.

    Args:
        query (str): El término de búsqueda para buscar en Wikipedia.

    Returns:
        str: El primer tercio del extracto introductorio del artículo de Wikipedia
             en español que coincide con la consulta, o "No se encontró información
             en Wikipedia." si la búsqueda no arroja resultados relevantes.
    """
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
        extract = extract[:tercio_len]  # Recorte del texto para no ocupar muchos tokens -> la info importante siempre esta al principio
    
    return extract

def buscar_y_mostrar_imagen(nombre_persona, nombre_archivo="imagen_resultado.jpg"):
    """
    Busca la primera imagen en Google Images para un nombre de persona dado,
    la descarga y la guarda en un archivo local.

    Utiliza la API de Búsqueda Personalizada de Google para la búsqueda de imágenes.
    Requiere una clave de API (archivo .env) y un ID de motor de búsqueda personalizado.

    Args:
        nombre_persona (str): El nombre de la persona o entidad para la que se buscarán imágenes.
        nombre_archivo (str, optional): El nombre del archivo local donde se guardará la imagen descargada.
                                        Por defecto, la imagen se guarda como "imagen_resultado.jpg".

    Returns:
        str: Un mensaje que describe el resultado de la operación:
             - La URL de la imagen encontrada si la búsqueda y descarga fueron exitosas.
             - "No se encontraron imágenes para la consulta." si la API no devuelve resultados.
             - Un mensaje de error detallado si ocurre alguna excepción durante el proceso.

    Raises:
        requests.exceptions.HTTPError: Se captura internamente si la petición a la API de Google
                                       o la descarga de la imagen resultan en un error HTTP (ej., 404, 500).
        Exception: Se captura internamente para cualquier otro error inesperado (ej., problemas de red,
                   JSON inválido, problemas al guardar el archivo).
    """
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

    """
    Realiza una búsqueda de similitud semántica en una colección de documentos
    utilizando embeddings vectoriales.

    Primero, convierte la pregunta del usuario en un vector (embedding). Luego,
    busca los documentos más similares a este embedding en la base de datos
    vectorial (`chromadb`). Devuelve la información de los documentos
    encontrados (título, fecha, enlace) formateada como una cadena de texto.

    Args:
        pregunta (str): La pregunta del usuario que se utilizará para buscar
                        documentos similares.

    Returns:
        str: Una cadena de texto que contiene la información formateada de los
             documentos de noticias más relevantes encontrados. Si no se encuentran
             documentos, retorna el mensaje "No se encontraron noticias similares.".
    """

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

    """
    Coordina y ejecuta múltiples análisis sobre un texto de consulta (noticia),
    utilizando diferentes agentes de LangChain, un modelo de lenguaje directo
    y una función de análisis de sentimiento personalizada.

    Combina los resultados de estos análisis en un único diccionario y lo devuelve
    como una respuesta JSON. Está diseñado para procesar el texto de una noticia
    y extraer diversas perspectivas (sesgos, polarizacion y sentimientos) de forma orquestada.

    Args:
        query (str): El texto de la noticia o consulta a ser analizada.

    Returns:
        JSONResponse: Un objeto de respuesta HTTP que contiene un diccionario JSON
                      con los resultados combinados de todos los análisis.
                      Si ocurre un error al decodificar JSON de alguna respuesta,
                      retorna un JSONResponse con un código de estado 500 y un mensaje de error.
    """

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
        # Si alguna de las respuestas (response_a, response_b, response_c) no es un JSON válido,
        # se captura el error y se devuelve una respuesta HTTP con un código de estado 500
        # y un mensaje de error que indica el problema.
        return JSONResponse(
            status_code=500,
            content={
                "error": "Alguna respuesta no es JSON válido",
                "detalle": str(e)
            }
        )

