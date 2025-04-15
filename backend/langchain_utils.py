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

# Inicializar cliente con persistencia
client = chromadb.PersistentClient(path="./chroma_db")  
doc_collection = client.get_or_create_collection("prototipoDB")
num_docs = doc_collection.count()
print(f"Documentos en la colección: {num_docs}")
embeddings = OpenAIEmbeddings(openai_api_key=settings.API_GPT)


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
    return page.get('extract', "No se encontró información en Wikipedia.")

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
            #display(imagen)
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

        r += f"Noticia {i+1}: {titulo} | {fecha} | {link} | {texto}\n"

    return r

        
# Crear una Tool para LangChain
buscar_por_embeddings_tool = Tool(
    name="BuscarPorEmbeddings",
    func=lambda x: buscar_por_embeddings(x, doc_collection),  # doc_collection es la colección de ChromaDB
    description="Busca documentos relevantes en ChromaDB utilizando embeddings calculados de la pregunta."
)

# Función para búsqueda en ChromaDB
def chromadb_search(query):
    resultados = buscar_por_embeddings(query, doc_collection, top_n=3)  # Función previamente definida
    return "\n".join([f"Noticia {i+1}:\nDocumento: {doc['documento']}\nMetadatos: {doc['metadatos']}\n{'-'*20}" 
                      for i, doc in enumerate(resultados)])

# Crear las herramientas
tools = [
    Tool(
        name="buscar_por_embeddings",
        func=buscar_por_embeddings,
        description="""
            Busca documentos relevantes en ChromaDB utilizando embeddings calculados de la pregunta.
            Cuando llames a esta herramienta el Action Input es solo el texto de la pregunta en string.
        """
    )
]

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
    )
]

# Definir el prompt usando PromptTemplate
prompt_template = """
Eres un agente de inteligencia artificial que responde en español. El usuario te entregará una noticia. Tu tarea es analizarla y entregar una respuesta estructurada en formato JSON con los siguientes elementos:

1. **Titular** de la noticia.
2. **Actores principales** (máximo 3 personas, deben ser personas individuales no grupos, ni entidades). Para cada uno, entrega:
   - Nombre completo.
   - Foto (usando la herramienta `buscar_y_mostrar_magen`).
   - Postura frente al hecho.
   - Perfil profesional o rol (usa `Wikipedia Search` si es necesario).
3. **Análisis crítico** en un párrafo que aborde:
   - Sesgos presentes (políticos, ideológicos, etc.).
   - Lenguaje cargado o emotivo.
   - Presencia o no de propaganda, con explicación.
   - Elementos faltantes o poco claros en la información entregada.
4. **Noticias similares** (máximo 3) para contrastar. Usa `buscar_por_embeddings`. Para cada una incluye:
   - Titular.
   - Resumen breve.
   - Enlace.

### Herramientas disponibles:
- `Wikipedia Search`: para obtener información sobre personas mencionadas.
- `buscar_y_mostrar_magen`: para encontrar imágenes de los actores principales.
- `buscar_por_embeddings`: para recuperar noticias similares de una base de datos (esta herramienta devuelve: titular, noticia, fecha y enlace).

### Reglas importantes:
- Solo utiliza la información proporcionada por el usuario o recuperada con las herramientas indicadas.
- No inventes datos.
- Si no encuentras información para un actor o una noticia similar, omítela en el JSON (no incluyas valores ficticios, deja el campo vacio).
- La respuesta debe ser un **JSON válido y bien formado**. No incluyas texto adicional fuera del JSON.

### Formato de respuesta:

{
  "titular": "Título de la noticia principal",
  "actores_principales": [
    {
      "nombre": "Nombre del actor",
      "foto_url": "https://link-a-la-foto.jpg",
      "postura": "Resumen de su postura frente al tema",
      "perfil": "Ej. presidente de Chile, periodista, activista"
    }
    // Puedes incluir hasta 3 actores, pero menos si no hay más información
  ],
  "analisis_critico": {
    "sesgo": "Ej. político, ideológico, económico, etc.",
    "lenguaje_cargado": "Ejemplos concretos del lenguaje usado",
    "propaganda": "sí/no + explicación",
    "faltante_informacion": "Aspectos clave que no se mencionan"
  },
  "noticias_similares": [
    {
      "titular": "Título de noticia similar",
      "resumen": "Breve explicación de su contenido",
      "enlace": "https://enlace-a-noticia.com"
    }
    // Máximo 3 noticias. Si no hay 3 relevantes, incluye menos.
  ]
}
"""

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

