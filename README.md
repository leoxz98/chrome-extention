# Prototipo Lectura Crítica

## 📝 Descripción

Este proyecto de tesis presenta un prototipo de extensión para navegador web diseñado para realizar un **análisis crítico automatizado de artículos noticiosos**. Su objetivo principal es fomentar una lectura más informada y consciente, ayudando a los usuarios a identificar y comprender diversos aspectos del contenido mediático. La herramienta se basa en la integración de **modelos de lenguaje de última generación (LLMs)** y un **sistema RAG (Retrieval-Augmented Generation)**, combinando capacidades avanzadas de generación de texto con información contextual. La extensión es capaz de identificar sesgos, inclinaciones ideológicas, tono del discurso y otros indicadores clave, mostrando al usuario métricas numéricas y visuales para apoyar una interpretación crítica de la noticia. Este desarrollo busca contribuir significativamente a la alfabetización mediática y al combate de la infoxicación y la desinformación en entornos digitales.

---

## 🚀 Características

- ✅ **Análisis de Noticia con un Clic:** Obtén un análisis crítico detallado de cualquier artículo noticioso directamente desde tu navegador.
- ✅ **Análisis Basado en IA con Contexto:** Utiliza modelos de lenguaje avanzados y un sistema RAG para proporcionar un análisis profundo de sesgos, tono y postura.
- ✅ **Chatea sobre la Noticia con la IA:** Interactúa con un asistente de IA para obtener más información o clarificar puntos específicos del análisis o de la noticia.
- ✅ **Visualización de Métricas Clave:** Presenta métricas numéricas y visuales (gráficos de sentimiento, polarización) para una interpretación rápida y efectiva.
- ✅ **Identificación de Actores y Sesgos:** Destaca los actores principales de la noticia con su postura y perfil, y enumera los sesgos detectados con explicaciones.
- ✅ **Noticias Similares por Semántica:** Encuentra artículos relacionados utilizando búsqueda por embeddings para ofrecer un contexto más amplio.
- ✅ **Generación de PDF:** La extensión puede generar un reporte en formato PDF de los resultados del análisis.

---

## 🛠 Tecnologías Utilizadas

### Backend (Python)

- **Python**
- **FastAPI**
- **Uvicorn**
- **LangChain**
- **OpenAI Python Client**
- **ChromaDB**
- **Hugging Face Transformers**
- **SpaCy**
- **Requests**
- **Pydantic y Pydantic-Settings**
- **Collections**

### Frontend (Extensión de Navegador)

- **JavaScript**
- **HTML**
- **CSS**
- **Chart.js**
- **html2pdf.js**

---

## 📦 Instalación y Ejecución

### 1. Clonar el Repositorio

```bash
git clone https://github.com/leoxz98/chrome-extention
cd chrome-extention
````

### 2. Configurar Variables de Entorno (.env)

Para que el backend funcione correctamente, necesitas configurar tus claves de API y otros parámetros. Crea un archivo llamado `.env` en la raíz de la carpeta `backend/` y en `backend/chroma_db` con el siguiente contenido:

```env
API_GPT="tu_clave_de_openai_aqui"
API_GOOGLE="tu_clave_de_api_de_google_aqui"
ID_GOOGLE="tu_id_de_motor_de_busqueda_personalizado_de_google_aqui"
PORT="8000"
DEBUG="True"
```

Asegúrate de reemplazar los valores de ejemplo con tus credenciales reales.

### 3. Descargar el Modelo de SpaCy

```bash
python -m spacy download es_core_news_sm
```

### 4. Ejecutar el Servidor Backend

Desde la carpeta `backend/`, inicia el servidor FastAPI usando Uvicorn:

```bash
uvicorn main:app --reload
```

Esto iniciará el servidor en `http://127.0.0.1:8000`. El flag `--reload` es útil durante el desarrollo.

---

## 🧩 Agregar la Extensión al Navegador (Google Chrome)

### 1. Abrir la Página de Extensiones

En Chrome, escribe en la barra de direcciones:

```
chrome://extensions
```

### 2. Activar el Modo Desarrollador

Activa el interruptor "Modo de desarrollador" (esquina superior derecha).

### 3. Cargar la Extensión Descomprimida

Haz clic en el botón **"Cargar descomprimida"**, navega hasta la carpeta `extension/` dentro del repositorio, y haz clic en **"Seleccionar carpeta"**.


