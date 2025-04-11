document.addEventListener("DOMContentLoaded", () => {
  let canAccessResult = false;
  let canAccessChat = false;

  // Elementos
  const sectionHome = document.getElementById("section-home");
  const sectionResult = document.getElementById("section-result");
  const sectionChat = document.getElementById("section-chat");

  const homeBtn = document.getElementById("btn-home");
  const resultBtn = document.getElementById("btn-result");
  const chatBtn = document.getElementById("btn-chat");
  const sendBtn = document.getElementById("send-btn");
  const autoBtn = document.getElementById("auto-btn");

  const textarea = document.getElementById("input-text");
  const resultOutput = document.getElementById("result-text");
  const statusMsg = document.getElementById("status-msg");

  // Función para mostrar secciones
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

  // Mostrar inicio al cargar
  showSection("home");

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

  // Enviar texto al backend
  sendBtn.addEventListener("click", async () => {
    const text = textarea.value.trim();

    if (!text) {
      statusMsg.textContent = "⚠️ El texto está vacío.";
      return;
    }

    statusMsg.textContent = "⏳ Enviando...";

    try {
      const response = await fetch("http://localhost:8000/analyze", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ text })
      });

      const data = await response.json();
      resultOutput.textContent = data.result;

      canAccessResult = true;
      canAccessChat = true;

      showSection("result");
      statusMsg.textContent = "✅ Análisis completado.";
    } catch (error) {
      console.error("Error al comunicarse con el backend:", error);
      statusMsg.textContent = "❌ Error al conectar con el backend.";
    }
  });

  // Auto-rellenar desde content-script
  autoBtn.addEventListener("click", () => {
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      chrome.scripting.executeScript({
        target: { tabId: tabs[0].id },
        files: ["content-script.js"]
      });
    });
  });

  // Recibir texto del content-script
  chrome.runtime.onMessage.addListener((message) => {
    if (message.action === "autoFill") {
      textarea.value = message.content;
    }
  });
});


// Escuchar el mensaje con el texto extraído
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === "autoFill") {
    const textarea = document.getElementById("input-text");  // Asegúrate de que este ID exista en tu HTML
    if (textarea) {
      textarea.value = message.content;  // Poner el contenido extraído en el campo de texto
    }
  }
});
