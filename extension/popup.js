function showSection(sectionId) {
  const sections = document.querySelectorAll('.section');
  sections.forEach(section => section.classList.add('hidden'));
  document.getElementById(sectionId).classList.remove('hidden');
}

// Botones de navegación
document.getElementById('btn-home').addEventListener('click', () => {
  showSection('section-home');
});

document.getElementById('btn-result').addEventListener('click', () => {
  showSection('section-result');
});

document.getElementById('btn-chat').addEventListener('click', () => {
  showSection('section-chat');
});


// Enviar texto al backend
document.getElementById('send-btn').addEventListener('click', () => {
  const inputText = document.getElementById('input-text').value;
  const statusMsg = document.getElementById('status-msg');

  if (!inputText.trim()) {
    statusMsg.textContent = "⚠️ El texto está vacío.";
    return;
  }

  statusMsg.textContent = "⏳ Enviando...";

  fetch(' http://127.0.0.1:8000/analyze', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ text: inputText })
  })
  .then(response => response.json())
  .then(data => {
    document.getElementById('result-text').textContent = data.result || "Sin respuesta del backend.";
    showSection('section-result');
    statusMsg.textContent = "✅ Análisis completado.";
  })
  .catch(error => {
    console.error(error);
    statusMsg.textContent = "❌ Error al conectar con el backend.";
  });
});