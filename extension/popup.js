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
      llenarResultados(data.savedResult);
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
      llenarResultados(data)
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
document.getElementById('descargar-btn').addEventListener('click', function() {
  chrome.storage.local.get('savedResult', function(result) {
      if (result.savedResult) {
          const dataStr = JSON.stringify(result.savedResult, null, 2);
          //const blob = new Blob([dataStr], { type: "application/json" });
          const blob = new Blob([dataStr], { type: "text/plain" });

          const url = URL.createObjectURL(blob);

          const a = document.createElement('a');
          a.href = url;
          a.download = 'analisis critico.txt';
          document.body.appendChild(a);
          a.click();
          document.body.removeChild(a);
          URL.revokeObjectURL(url);
      } else {
          alert('No hay datos guardados aún.');
      }
  });
});



function llenarResultados(data) {
  // Llenar el titular
  const titularDiv = document.getElementById('titular');
  titularDiv.textContent = data.titular;

  // Llenar actores principales
  const actoresContainer = document.getElementById('actores-container');
  actoresContainer.innerHTML = ''; // Limpiar primero
  data.actores_principales.forEach(actor => {
    const actorDiv = document.createElement('div');
    actorDiv.classList.add('actor');
    actorDiv.innerHTML = `
      <img src="${actor.foto_url}" alt="${actor.nombre}" width="80" height="80" style="border-radius: 50%; object-fit: cover;">
      <h5>${actor.nombre}</h5>
      <p><strong>Postura:</strong> ${actor.postura}</p>
      <p><strong>Perfil:</strong> ${actor.perfil}</p>
    `;
    actoresContainer.appendChild(actorDiv);
  });

  // Llenar gráficos
  // Sentimientos
  const sentimientosData = data.analisis_critico.analisis_sentimiento.proporcion_sentimientos;
  new Chart(document.getElementById('sentimientoChart'), {
    type: 'pie',
    data: {
      labels: Object.keys(sentimientosData),
      datasets: [{
        data: Object.values(sentimientosData),
        backgroundColor: ['#FFCC00', '#FF3300', '#66CC66']
      }]
    },
    options: {
      responsive: false
    }
  });

  // Discurso de odio
  const hateData = data.analisis_critico.analisis_profundo.hate_speech;
  new Chart(document.getElementById('hateSpeechChart'), {
    type: 'pie',
    data: {
      labels: Object.keys(hateData),
      datasets: [{
        data: Object.values(hateData),
        backgroundColor: ['#FF6666', '#FF9933', '#FFCC99']
      }]
    },
    options: {
      responsive: false
    }
  });

  // Emociones
  const emocionesData = data.analisis_critico.analisis_profundo.emotion;
  new Chart(document.getElementById('emocionesChart'), {
    type: 'pie',
    data: {
      labels: Object.keys(emocionesData),
      datasets: [{
        data: Object.values(emocionesData),
        backgroundColor: [
          '#99CCFF', '#66FF66', '#FF6666', '#FF9933', '#CCCCCC', '#9966CC', '#FFFF66'
        ]
      }]
    },
    options: {
      responsive: false
    }
  });

  // Ironía
  const ironiaData = data.analisis_critico.analisis_profundo.irony;
  new Chart(document.getElementById('ironiaChart'), {
    type: 'pie',
    data: {
      labels: Object.keys(ironiaData),
      datasets: [{
        data: Object.values(ironiaData),
        backgroundColor: ['#66CCFF', '#FF99CC']
      }]
    },
    options: {
      responsive: false
    }
  });

  // Llenar noticias similares
  const noticiasContainer = document.getElementById('noticias-similares');
  noticiasContainer.innerHTML = '';
  data.noticias_similares.forEach(noticia => {
    const noticiaDiv = document.createElement('div');
    noticiaDiv.classList.add('noticia');
    noticiaDiv.innerHTML = `
      <a href="${noticia.enlace}" target="_blank">${noticia.titular}</a>
    `;
    noticiasContainer.appendChild(noticiaDiv);
  });
}



