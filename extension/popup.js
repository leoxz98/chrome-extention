let sentimientoChartInstance = null;
let polarizacionChartInstance = null;

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
      alert(JSON.stringify(data, null, 2));
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
  // Destruir instancias previas si existen
  if (sentimientoChartInstance) {
    sentimientoChartInstance.destroy();
  }
  if (polarizacionChartInstance) {
    polarizacionChartInstance.destroy();
  }
  // Llenar el titular
  const titularDiv = document.getElementById('titular');
  titularDiv.textContent = data.titular;
  const resumenDiv = document.getElementById('resumen');
  resumenDiv.textContent = data.resumen;
  // Llenar el resumen
  document.getElementById('resumen').textContent = data.resumen;

  // Llenar actores principales
  const actoresContainer = document.getElementById('actores-container');
  actoresContainer.innerHTML = '';
  data.actores_principales.forEach(actor => {
    const actorDiv = document.createElement('div');
    actorDiv.classList.add('actor');
    actorDiv.innerHTML = `
    <div style="text-align: center;">
      <img src="${actor.foto_url}" alt="${actor.nombre}" width="80" height="80" style="border-radius: 50%; object-fit: cover; display: block; margin: 0 auto;">
      <h5 style="margin: 10px 0 5px;">${actor.nombre}</h5>
    </div>
    <p><strong>Postura:</strong> ${actor.postura}</p>
    <p><strong>Perfil:</strong> ${actor.perfil}</p>
  `;
  
    actoresContainer.appendChild(actorDiv);
  });

 // Gráfico de sentimientos
 const sentimientosData = data.proporcion_sentimientos;
 const ctxSentimiento = document.getElementById('sentimientoChart').getContext('2d');
 sentimientoChartInstance = new Chart(ctxSentimiento, {
   type: 'pie',
   data: {
     labels: Object.keys(sentimientosData),
     datasets: [{
       data: Object.values(sentimientosData),
       backgroundColor: ['#FFCC00', '#FF3300', '#66CC66']
     }]
   },
   options: {
    plugins: {
      title: {
        display: true,
        text: 'Proporción de Sentimientos',
        font: {
          size: 16
        },
        padding: {
          top: 0,
          bottom: 0
        }
      },
      // ...otros plugins
    },
    responsive: false
   }
 });

 // Índice de polarización
  const indicePolarizacion = data.indice_polarizacion * 100; 
 // const indicePolarizacion = 55; 

 let color;
 if (indicePolarizacion < 33) {
   color = '#66CC66';
 } else if (indicePolarizacion < 66) {
   color = '#FFCC00';
 } else {
   color = '#FF3300';
 }

 const ctxPolarizacion = document.getElementById('polarizacionChart').getContext('2d');
 polarizacionChartInstance = new Chart(ctxPolarizacion, {
   type: 'bar',
   data: {
     labels: ['Índice de polarización'],
     datasets: [{
       data: [indicePolarizacion],
       backgroundColor: [color],
       barThickness: 30,
     }]
   },
   options: {
     indexAxis: 'y',
     scales: {
       x: {
         max: 100,
         min: 0,
         ticks: {
           callback: function (value) {
             return value + '%';
           }
         }
       },
       y: {
         display: false
       }
     },
     plugins: {
      title: {
        display: true,
        text: 'Polarización',
        font: {
          size: 16
        },
        padding: {
          top: 10,
          bottom: 10
        }
      },
       legend: {
         display: false
       },
       tooltip: {
         callbacks: {
           label: (context) => context.parsed.x.toFixed(2) + '%'
         }
       }
     },
     responsive: false
   }
 });


  // Llenar noticias similares
  const noticiasContainer = document.getElementById('noticias-similares');
  noticiasContainer.innerHTML = '';
  data.noticias_similares.forEach(noticia => {
    const noticiaDiv = document.createElement('div');
    noticiaDiv.classList.add('noticia');
    noticiaDiv.innerHTML = `<a href="${noticia.enlace}" target="_blank">${noticia.titular}</a>`;
    noticiasContainer.appendChild(noticiaDiv);
  });


  const sesgos = data.sesgos;

  // Lectura de mente
  const lecturaSpan = document.getElementById('lectura-mente-ejemplo');
  if (sesgos.lectura_de_mente.presente && sesgos.lectura_de_mente.ejemplos.length > 0) {
    lecturaSpan.textContent = sesgos.lectura_de_mente.ejemplos.join(', ');
  } else {
    lecturaSpan.textContent = 'No se detectó este sesgo.';
  }
  
  // Opiniones como hechos
  const opinionesSpan = document.getElementById('opiniones-hechos-ejemplo');
  if (sesgos.opiniones_como_hechos.presente && sesgos.opiniones_como_hechos.ejemplos.length > 0) {
    opinionesSpan.textContent = sesgos.opiniones_como_hechos.ejemplos.join(', ');
  } else {
    opinionesSpan.textContent = 'No se detectó este sesgo.';
  }
  
  // Sensacionalismo / emocionalismo
  const sensaSpan = document.getElementById('sensacionalismo-ejemplo');
  if (sesgos.sensacionalismo_emocionalismo.presente && sesgos.sensacionalismo_emocionalismo.ejemplos.length > 0) {
    sensaSpan.textContent = sesgos.sensacionalismo_emocionalismo.ejemplos.join(', ');
  } else {
    sensaSpan.textContent = 'No se detectó este sesgo.';
  }
  


}




