document.addEventListener("DOMContentLoaded", () => {
  // Variables auxiliares
  let canAccessResult = false;
  let canAccessChat = false;

  // Elementos del html
  const sectionHome = document.getElementById("section-home");
  const sectionResult = document.getElementById("section-result");
  const sectionChat = document.getElementById("section-chat");

  const homeBtn = document.getElementById("btn-home");
  const resultBtn = document.getElementById("btn-result");
  const chatBtn = document.getElementById("btn-chat");
  const sendBtn = document.getElementById("send-btn");
  const autoBtn = document.getElementById("auto-btn");
  const clearBtn = document.getElementById("clear-btn");

  const textarea = document.getElementById("input-text");
  //const resultOutput = document.getElementById("result-text");
  const statusMsg = document.getElementById("status-msg");

  const titularElem = document.getElementById("titular");
  const actoresContainer = document.getElementById("actores-container");
  const analisisUl = document.getElementById("analisis-critico");
  const similaresContainer = document.getElementById("noticias-similares");

  // Cambiar entre secciones
  function showSection(sectionId) {
    sectionHome.classList.add("hidden");
    sectionResult.classList.add("hidden");
    sectionChat.classList.add("hidden");

    switch (sectionId) {
      case "home":
        sectionHome.classList.remove("hidden");
        break;
      case "result":
        sectionResult.classList.remove("hidden");
        break;
      case "chat":
        sectionChat.classList.remove("hidden");
        break;
    }
  }

  // Restaurar datos desde chrome.storage al cargar
  chrome.storage.local.get(["savedText", "savedResult"], (data) => {
    if (data.savedText) {
      textarea.value = data.savedText;
      canAccessResult = true;
      canAccessChat = true;
    }

    if (data.savedResult) {
      mostrarResultados(data.savedResult);
    }
  });

  // Guardar automáticamente mientras el usuario escribe
  textarea.addEventListener("input", () => {
    chrome.storage.local.set({ savedText: textarea.value });
  });

  // Navegación
  homeBtn.addEventListener("click", () => showSection("home"));
  resultBtn.addEventListener("click", () => {
    if (canAccessResult) {
      showSection("result");
    } else {
      alert("Primero debes enviar un texto para analizar.");
    }
  });
  chatBtn.addEventListener("click", () => {
    if (canAccessChat) {
      showSection("chat");
    } else {
      alert("Primero debes enviar un texto para habilitar el chat.");
    }
  });

  // Enviar data al backend
  sendBtn.addEventListener("click", async () => {
    const text = textarea.value.trim();

    if (!text) {
      statusMsg.textContent = "⚠️ El texto está vacío.";
      return;
    }

    statusMsg.textContent = "⏳ Enviando...";

    try {
      const response = await fetch("http://127.0.0.1:8000/analyze", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ text })
      });

      const data = await response.json();
      const resultText = JSON.stringify(data.result);
      
      //resultOutput.textContent = resultText;
      mostrarResultados(data)
      chrome.storage.local.set({ savedResult: data });

      canAccessResult = true;
      canAccessChat = true;

      showSection("result");
      statusMsg.textContent = "✅ Análisis completado.";
    } catch (error) {
      console.error("Error al comunicarse con el backend:", error);
      statusMsg.textContent = "❌ Error al conectar con el backend.";
    }
  });

  // Botón para obtener la noticia automatica 
  autoBtn.addEventListener("click", () => {
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      chrome.scripting.executeScript({
        target: { tabId: tabs[0].id },
        files: ["content-script.js"]
      });
    });
  });

  // borrar todo
  clearBtn.addEventListener("click", () => {
    textarea.value = "";
    //resultOutput.textContent = "Aquí se mostrará el análisis...";
    chrome.storage.local.remove(["savedText", "savedResult"]);
    canAccessResult = false;
    canAccessChat = false;
    showSection("home");
    statusMsg.textContent = "🧹 Se borraron los datos.";
  });

  // Recibir de content-script
  chrome.runtime.onMessage.addListener((message) => {
    if (message.action === "autoFill") {
      textarea.value = message.content;
      chrome.storage.local.set({ savedText: message.content });
    }
  });
});


// asdasdsa

function mostrarResultados(data) {
  // Titular
  document.getElementById("titular").textContent = data.titular;

  // Actores principales
  const actoresContainer = document.getElementById("actores-container");
  actoresContainer.innerHTML = "";
  data.actores_principales.forEach(actor => {
    const actorDiv = document.createElement("div");
    actorDiv.classList.add("actor-card");
  
    actorDiv.innerHTML = `
      <img src="${actor.foto_url}" alt="Foto de ${actor.nombre}" />
      <h5>${actor.nombre}</h5>
      <p><em>${actor.perfil}</em></p>
      <p>${actor.postura}</p>
    `;
  
    actoresContainer.appendChild(actorDiv);
  });
  

  // Análisis crítico
  const analisis = data.analisis_critico;
  const analisisUl = document.getElementById("analisis-critico");
  analisisUl.innerHTML = `
    <li><strong>Sesgo:</strong> ${analisis.sesgo}</li>
    <li><strong>Lenguaje cargado:</strong> ${analisis.lenguaje_cargado}</li>
    <li><strong>Propaganda:</strong> ${analisis.propaganda}</li>
    <li><strong>Falta de información:</strong> ${analisis.faltante_informacion}</li>
  `;

  // Noticias similares
  const similaresContainer = document.getElementById("noticias-similares");
  similaresContainer.innerHTML = "";
  data.noticias_similares.forEach(not => {
    const notDiv = document.createElement("div");
    notDiv.classList.add("noticia");

    notDiv.innerHTML = `
      <p><strong>${not.titular}</strong></p>
      <p>${not.resumen}</p>
      <a href="${not.enlace}" target="_blank">Leer más</a>
    `;

    similaresContainer.appendChild(notDiv);
  });
}
