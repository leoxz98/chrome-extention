// Inicializacon de variables 
let sentimientoChartInstance = null;
let polarizacionChartInstance = null;
let history = [];
let textoCompartir;

document.addEventListener("DOMContentLoaded", () => {
  // Variables auxiliares
  let canAccessResult = false;
  let canAccessChat = false;
  let canAccessShare = false;
  let firstMjs = true;
  let text;
  const chatsendbutton = document.getElementById("send")

  // Elementos del html
  const sectionHome = document.getElementById("section-home");
  const sectionResult = document.getElementById("section-result");
  const sectionChat = document.getElementById("section-chat");
  const sectionShare = document.getElementById("section-share")
  const homeBtn = document.getElementById("btn-home");
  const resultBtn = document.getElementById("btn-result");
  const chatBtn = document.getElementById("btn-chat");
  const sendBtn = document.getElementById("send-btn");
  const autoBtn = document.getElementById("auto-btn");
  const clearBtn = document.getElementById("clear-btn");
  const shareBtn = document.getElementById("share-btn")
  const textarea = document.getElementById("input-text");
  const whatsappBtn = document.getElementById("cwsp");
  const xBtn = document.getElementById("cx");
  const statusMsg = document.getElementById("status-msg");

  // Cambiar entre pestañas
  function showSection(sectionId) {
    sectionHome.classList.add("hidden");
    sectionResult.classList.add("hidden");
    sectionChat.classList.add("hidden");
    sectionShare.classList.add("hidden")
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
      case "share":
        sectionShare.classList.remove("hidden");
        break;
    }
  }

  // Restaurar datos desde chrome.storage al cargar
  chrome.storage.local.get(["savedText", "savedResult", "chatHistory"], (data) => {
    if (data.savedText) {
      textarea.value = data.savedText;
      text = data.savedText;
      canAccessResult = true;
      canAccessChat = true;
      canAccessShare = true;
    }
  
    if (data.savedResult) {
      llenarResultados(data.savedResult);
      textoCompartir = data.savedResult;
    }
  
    if (data.chatHistory && Array.isArray(data.chatHistory)) {
      //alert(data.chatHistory);
      history = data.chatHistory.filter(
        (item) =>
          Array.isArray(item) &&
          item.length === 2 &&
          typeof item[0] === "string" &&
          typeof item[1] === "string"
      );
      renderMessages();
    } else {
      history = [];
    }
  });
  

  // Guardar automáticamente mientras el usuario escribe
  textarea.addEventListener("input", () => {
    chrome.storage.local.set({ savedText: textarea.value });
  });

  // Navegación entre pestañas
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
  shareBtn.addEventListener("click", () => {
    if (canAccessShare){
      showSection("share");
    } else{
      alert("Primero debes enviar un texto para habilitar el compartir.")
    }
  });

  // Enviar data al backend
  sendBtn.addEventListener("click", async () => {
    text = textarea.value.trim();
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
      llenarResultados(data)
      textoCompartir = data;
      chrome.storage.local.set({ savedResult: data });

      canAccessResult = true;
      canAccessChat = true;
      canAccessShare = true;

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
    chrome.storage.local.remove(["savedText", "savedResult", "chatHistory"]);
    canAccessResult = false;
    canAccessChat = false;
    canAccessShare = false;
    firstMjs = true;
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

//

document.getElementById("send").addEventListener("click", async () => {
  const input = document.getElementById("user-input").value.trim();
  //alert(firstMjs);

  if (!input) return;

  if (firstMjs) {
    history.push(["system", text]);  // Adjunta contexto
    firstMjs = false;
  }

  history.push(["user", input]);
  renderMessages();
  document.getElementById("user-input").value = "";

  const res = await fetch("http://127.0.0.1:8000/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      message: input,
      history: history,
    }),
  });

  const data = await res.json();
  history.push(["assistant", data.reply]);
  chrome.storage.local.set({ chatHistory: history });  // Guardar el historial actualizado
  renderMessages();
});

// seccion de compartir en redes sociales

whatsappBtn.addEventListener("click", () => {
  chrome.tabs.query({ active: true, currentWindow: true }, function(tabs) {
    const url = tabs[0].url;

    let texto = generarTextoCompartible(textoCompartir, url); 
    let w = 'https://web.whatsapp.com/send?text=' + encodeURIComponent(texto);
    window.open(w, '_blank');
  });
});

xBtn.addEventListener("click", () => {
  chrome.tabs.query({ active: true, currentWindow: true }, function(tabs) {
    const url = tabs[0].url;

    let texto = generarTextoCompartible(textoCompartir, url);
    let tweet = 'https://twitter.com/intent/tweet?text=' + encodeURIComponent(texto);

    window.open(tweet, '_blank');
  });
});



});

// Seccion de descarga
document.getElementById('djson').addEventListener('click', function() {
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

document.getElementById("dpdf").addEventListener("click", () => {
  //alert("test");
  const element = document.getElementById("result-container");
  const wasHidden = element.classList.contains("hidden");
  if (wasHidden) element.classList.remove("hidden");

  setTimeout(() => {
    const opt = {
      margin: [0.5, 1, 0.5, 1], // top, left, bottom, right
      filename:     'analisis.pdf',
      image:        { type: 'jpeg', quality: 0.98 },
      html2canvas:  { scale: 2 },
      jsPDF:        { unit: 'in', format: 'letter', orientation: 'portrait' }
    };

    html2pdf().set(opt).from(element).save();

    if (wasHidden) element.classList.add("hidden");
  }, 100); 
});


function llenarResultados(data) {
  // Evitar error canvas ID en uso
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

// Convertir todas las imágenes primero y luego renderizar (sirve pal pdf)
Promise.all(
  data.actores_principales.map(async (actor) => {
    const base64Image = await toBase64(actor.foto_url);

    const actorDiv = document.createElement('div');
    actorDiv.classList.add('actor');
    actorDiv.innerHTML = `
      <div style="text-align: center;">
        <img src="${base64Image}" alt="${actor.nombre}" width="80" height="80" style="border-radius: 50%; object-fit: cover; display: block; margin: 0 auto;">
        <h5 style="margin: 10px 0 5px;">${actor.nombre}</h5>
      </div>
      <p><strong>Postura:</strong> ${actor.postura}</p>
      <p><strong>Perfil:</strong> ${actor.perfil}</p>
    `;
    actoresContainer.appendChild(actorDiv);
  })
);

 // Gráfico de sentimientos
const sentimientosData = data.proporcion_sentimientos;
const ctxSentimiento = document.getElementById('sentimientoChart').getContext('2d');

// Orden y colores fijos: NEG → rojo, NEU → azul, POS → verde
const etiquetas = ['NEG', 'NEU', 'POS'];
const colores = {
  NEG: '#FF3300', // rojo
  NEU: '#3399FF', // azul
  POS: '#66CC66'  // verde
};

const valores = etiquetas.map(etiqueta => sentimientosData[etiqueta] || 0);
const coloresOrdenados = etiquetas.map(etiqueta => colores[etiqueta]);

sentimientoChartInstance = new Chart(ctxSentimiento, {
  type: 'pie',
  data: {
    labels: ['Negativo', 'Neutro', 'Positivo'],
    datasets: [{
      data: valores,
      backgroundColor: coloresOrdenados
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
      }
    },
    responsive: false
  }
});


 // Índice de polarización
  const indicePolarizacion = data.indice_polarizacion; 
 
// Función para calcular el color (rojo a verde)
  function polaridadToColor(valor) {
    // Normalizar de -1..1 a 0..1
    const normalized = (valor + 1) / 2;
    const red = Math.round(255 * (1 - normalized));
    const green = Math.round(255 * normalized);
    return `rgb(${red}, ${green}, 0)`;
  }

  const ctx = document.getElementById('polarizacionChart').getContext('2d');
  polarizacionChartInstance = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: ['Polaridad'],
      datasets: [{
        label: 'Valor de polaridad',
        data: [indicePolarizacion],
        backgroundColor: [polaridadToColor(indicePolarizacion)],
        borderColor: '#000',
        borderWidth: 1
      }]
    },
    options: {
      indexAxis: 'y',
      scales: {
        x: {
          min: -1,
          max: 1,
          title: {
            display: true,
            text: 'Polaridad (-1 = Negativo, 1 = Positivo)'
          }
        }
      },
      plugins: {
        legend: {
          display: false
        },
        tooltip: {
          callbacks: {
            label: function(context) {
              return 'Polaridad: ' + context.raw.toFixed(2);
            }
          }
        }
      }
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


const listaSesgos = document.getElementById('lista-sesgos');
listaSesgos.innerHTML = ''; // Limpiar lista antes de llenar

const sesgos = data.sesgos;

// Mapeo de nombres En:ES
const etiquetasSesgos = {
  "Unsubstantiated claims bias": "Afirmaciones sin fundamento",
  "Opinion statements presented as facts": "Opiniones como hechos",
  "Sensationalism or Emotionalism": "Sensacionalismo / emocionalismo",
  "Ad Hominem or Mudslinging": "Ataque personal",
  "Mind reading": "Lectura de mente",
  "Slant bias": "Sesgo de inclinación",
  "Subjective qualifying adjectives": "Adjetivos calificativos subjetivos",
  "Bias by labeling and word choice": "Etiquetado y elección de palabras",
  "Flawed logic": "Lógica defectuosa"
};

// Recorremos todos los sesgos
for (const clave in sesgos) {
  const sesgo = sesgos[clave];

  if (sesgo.presente && sesgo.porque.length > 0) {
    const li = document.createElement('li');
    li.innerHTML = `
      - <strong>${etiquetasSesgos[clave] || clave}</strong><br>
      <span>${sesgo.porque.join('<br>')}</span><br><br>
    `;
    listaSesgos.appendChild(li);
  }
}

// Si no se detectó ningún sesgo, mostrar mensaje
if (listaSesgos.children.length === 0) {
  const li = document.createElement('li');
  li.textContent = 'No se detectaron sesgos en el texto.';
  listaSesgos.appendChild(li);
}

}


// chat ia
function renderMessages() {
  const messagesDiv = document.getElementById("messages");
  messagesDiv.innerHTML = "";

  for (const [role, content] of history) {
    if (role === "system") continue;

    const messageBubble = document.createElement("div");
    messageBubble.classList.add("message-bubble", role);

    const label = role === "user" ? "Tú" : "GPT";
    messageBubble.innerHTML = `<strong>${label}:</strong> ${content}`;

    messagesDiv.appendChild(messageBubble);
  }

  // Opcional: desplazar hacia el final automáticamente
  messagesDiv.scrollTop = messagesDiv.scrollHeight;
}



// convertir imagen URL a base64 para pdf
function toBase64(url) {
  return new Promise((resolve) => {
    const img = new Image();
    img.crossOrigin = "Anonymous";
    img.onload = function () {
      const canvas = document.createElement("canvas");
      canvas.width = this.width;
      canvas.height = this.height;
      const ctx = canvas.getContext("2d");
      ctx.drawImage(this, 0, 0);
      resolve(canvas.toDataURL("image/png"));
    };
    img.onerror = function () {
      console.warn("No se pudo cargar la imagen:", url);
      resolve(""); // Devuelve string vacío si falla
    };
    img.src = url;
  });
}


// generar texto a compartir en redes
function generarTextoCompartible(data, url) {
  const actoresNombres = data.actores_principales.map(actor => actor.nombre).join(', ');
  const sentimientos = data.proporcion_sentimientos;
  const polarizacion = data.indice_polarizacion;

  const etiquetasSesgos = {
    "Unsubstantiated claims bias": "Afirmaciones sin fundamento",
    "Opinion statements presented as facts": "Opiniones como hechos",
    "Sensationalism or Emotionalism": "Sensacionalismo / emocionalismo",
    "Ad Hominem or Mudslinging": "Ataque personal",
    "Mind reading": "Lectura de mente",
    "Slant bias": "Sesgo de inclinación",
    "Subjective qualifying adjectives": "Adjetivos calificativos subjetivos",
    "Bias by labeling and word choice": "Etiquetado y elección de palabras",
    "Flawed logic": "Lógica defectuosa"
  };

  // Filtrar sesgos presentes y traducir nombres
  const sesgosPresentes = Object.entries(data.sesgos)
    .filter(([_, info]) => info.presente)
    .map(([claveOriginal, info]) => {
      const nombreTraducido = etiquetasSesgos[claveOriginal] || claveOriginal;
      const razones = info.porque.length > 0 ? `\n  - ${info.porque.join('\n  - ')}` : '';
      return `• ${nombreTraducido}${razones}`;
    });

  const textoSesgos = sesgosPresentes.length > 0
    ? `\n🧠 Sesgos detectados:\n${sesgosPresentes.join('\n')}`
    : '';

  return `
📎 Enlace: ${url}

📰 Titular: ${data.titular}

👥 Actores principales: ${actoresNombres}

📊 Sentimientos:
- Negativo: ${(sentimientos.NEG * 100).toFixed(1)}%
- Neutro: ${(sentimientos.NEU * 100).toFixed(1)}%
- Positivo: ${(sentimientos.POS * 100).toFixed(1)}%

⚖️ Índice de polarización: ${(polarizacion * 100).toFixed(1)}%${textoSesgos}
  `.trim();
}




