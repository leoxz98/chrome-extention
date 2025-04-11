// content-script.js

// Función para limpiar el contenido y eliminar los enlaces dentro del artículo
function cleanContent() {
    // Seleccionar el contenedor principal de contenido (Artículo o principal)
    const mainContent = document.querySelector('article') || document.querySelector('.main-content') || document.querySelector('[role="main"]');
  
    if (mainContent) {
      // Eliminar todos los enlaces dentro del contenedor principal (artículo)
      mainContent.querySelectorAll('a').forEach(link => link.remove());
      
      // Extraer solo el texto visible del contenedor principal
      return mainContent.innerText.trim();
    }
  
    // Si no se encuentra un contenedor específico, se extrae todo el texto del cuerpo
    // pero también eliminamos enlaces en el cuerpo entero
    document.querySelectorAll('a').forEach(link => link.remove());
    return document.body.innerText.trim();
  }
  
  // Ejecuta la extracción y envía el texto al popup.js
  const text = cleanContent();
  
  // Enviar el contenido extraído al popup.js para rellenar el campo de texto
  chrome.runtime.sendMessage({ action: "autoFill", content: text });
  