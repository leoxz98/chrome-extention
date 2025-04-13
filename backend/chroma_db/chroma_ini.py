import chromadb
from config_db import settings

client = chromadb.PersistentClient(path=".")

# Asegura la existencia de la colección (la crea solo si no existe)
collection = client.get_or_create_collection(
    name="prototipoDB",
    metadata={"dimension": 1536}  # Esto solo se aplica si se crea por primera vez
)

# Verificar el estado de la colección
num_docs = collection.count()
print(f"Documentos en la colección: {num_docs}")

# Guardar noticias a db

def savedocs():
    from langchain.embeddings import OpenAIEmbeddings
    import pandas as pd
    import uuid
    embeddings = OpenAIEmbeddings(openai_api_key=settings.API_GPT)
    df = pd.read_csv("noticias.csv",encoding="utf-8",sep=';')
    print("xd")
    print(df.columns)


    # Iterar sobre cada fila del csv
    for index, row in df.iterrows():
        texto = row['text']
        if not isinstance(texto, str) or texto.strip() == "":
            print(f"Fila {index}: el texto está vacío, se omite.")
            continue
        
        # Generar metadatos a partir del resto de columnas
        metadatos = row.drop(labels=['text']).to_dict()
        
        # Generar un UUID único para cada doc
        unique_id = str(uuid.uuid4())
        
        # Calcular embedding 
        embedding = embeddings.embed_query(texto)
        
        # Agregar el documento a ChromaDB
        collection.add(
            ids=[unique_id],  # Usar UUID como ID único
            documents=[texto],  # Documento principal
            embeddings=[embedding],  # Embedding generado
            metadatas=[metadatos]  # Metadatos asociados
        )

    print("Ok!!")

#savedocs()

results = collection.get(include=["documents", "metadatas", "embeddings"])

# Mostrar resultados
for i, doc in enumerate(results['documents']):
    print(f"\nDocumento {i+1}:")
    print(f"ID: {results['ids'][i]}")
    print(f"Texto: {doc}")
    print(f"Metadata: {results['metadatas'][i]}")
    # Puedes imprimir embeddings si los necesitas también
    # print(f"Embedding: {results['embeddings'][i]}")



