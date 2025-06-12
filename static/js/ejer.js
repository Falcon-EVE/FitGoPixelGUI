document.addEventListener("DOMContentLoaded", function () {
    const progressBar = document.getElementById("progress-bar");
    const timerDisplay = document.getElementById("timer-display");
    const startButton = document.getElementById("start-timer");
    const gifContainer = document.getElementById("gif-container");
    let timerInterval;
let timeLeft = 60; // 1 minuto en segundos

// Función para actualizar la cuenta regresiva y la barra de progreso
function updateTimer() {
  const minutes = Math.floor(timeLeft / 60);
  const seconds = timeLeft % 60;
  timerDisplay.textContent = `${minutes}:${seconds < 10 ? '0' : ''}${seconds}`;

  // Actualizar la barra de progreso
  const progress = (60 - timeLeft) / 60 * 100;
  progressBar.style.width = `${progress}%`;

  if (timeLeft <= 0) {
    clearInterval(timerInterval); // Detener el temporizador cuando llegue a cero
    startButton.disabled = false; // Habilitar el botón de nuevo
    startButton.style.opacity = "1"; // Volver a mostrar el botón
    startButton.textContent = "Reiniciar Temporizador"; // Cambiar el texto del botón
  } else {
    timeLeft--; // Reducir el tiempo restante
  }
}

// Función para mostrar el GIF durante 30 segundos
function showGif() {
  gifContainer.style.display = "block"; // Mostrar el GIF

  // Ocultar el GIF después de 30 segundos
  setTimeout(function() {
    gifContainer.style.display = "none"; // Ocultar el GIF
  }, 30000); // 30000 ms = 30 segundos
}

// Función para iniciar el temporizador
function startTimer() {
  timeLeft = 60; // Resetear el tiempo a 1 minuto
  progressBar.style.width = "0%"; // Resetear la barra de progreso
  timerDisplay.textContent = "1:00"; // Resetear el temporizador visualmente
  startButton.disabled = true; // Deshabilitar el botón una vez que se inicie
  startButton.style.opacity = "0.5"; // Hacer que el botón se vea deshabilitado

  timerInterval = setInterval(updateTimer, 1000); // Actualizar cada segundo

  showGif(); // Mostrar el GIF cuando se hace clic en "Comenzar"
}

startButton.addEventListener("click", startTimer); // Evento para iniciar el temporizador
    

});
