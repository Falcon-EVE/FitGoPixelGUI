document.addEventListener('DOMContentLoaded', () => {
    const modal = document.getElementById('warmup-modal');
    const yesButton = document.getElementById('warmup-yes');
    const noButton = document.getElementById('warmup-no');
    const warmupVideoContainer = document.getElementById('warmup-video-container');
    const warmupVideo = document.getElementById('warmup-video');
    const continueButton = document.getElementById('continue-button');
    const exerciseContent = document.getElementById('exercise-content');
    const exerciseVideoContainer = document.getElementById('exercise-video-container');
    const exerciseVideo = document.getElementById('exercise-video');
    const exerciseVideoSource = exerciseVideo.querySelector('source');
    const timerDisplay = document.getElementById('timer-display');
    const finishButton = document.getElementById('finish-exercise');
    const trainerSpeech = document.querySelector('.speech-bubble p');
    const circle = document.querySelector('.progress-ring-circle');
    const radius = circle.r.baseVal.value;
    const circumference = 2 * Math.PI * radius;

    circle.style.strokeDasharray = `${circumference} ${circumference}`;
    circle.style.strokeDashoffset = circumference;

    function setProgress(percent) {
        const offset = circumference - (percent / 100) * circumference;
        circle.style.strokeDashoffset = offset;
    }

    // Mostrar modal al cargar
    modal.style.display = 'block';
    exerciseContent.style.display = 'none';
    exerciseVideoContainer.style.display = 'none';

    // Botón "Sí": Mostrar video de calentamiento
    yesButton.addEventListener('click', () => {
        modal.style.display = 'none';
        warmupVideoContainer.style.display = 'block';
        warmupVideo.play();
        trainerSpeech.textContent = '¡Sigue el video para calentar!';
    });

    // Botón "No": Mostrar ejercicios directamente
    noButton.addEventListener('click', () => {
        modal.style.display = 'none';
        exerciseContent.style.display = 'block';
    });

    // Botón "Continuar": Ocultar video de calentamiento y mostrar ejercicios
    continueButton.addEventListener('click', () => {
        warmupVideoContainer.style.display = 'none';
        exerciseContent.style.display = 'block';
        warmupVideo.pause();
        trainerSpeech.textContent = '¡Vamos a ponernos fuertes! Elige un ejercicio y comienza lo bueno.';
    });

    // Función para actualizar monedas
    function updateMonedas() {
        fetch('/get_monedas', {
            method: 'GET',
            headers: { 'Content-Type': 'application/json' }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                document.getElementById('monedas').textContent = data.monedas;
            } else {
                console.error('Error al obtener monedas:', data.message);
            }
        })
        .catch(error => console.error('Error al actualizar monedas:', error));
    }

    // Función para iniciar el ejercicio
    window.startExercise = function(exerciseName, exerciseId, videoSrc) {
        // Ocultar ejercicios y mostrar video
        exerciseContent.style.display = 'none';
        exerciseVideoContainer.style.display = 'flex';
        exerciseVideoSource.src = videoSrc;
        exerciseVideo.load(); // Recargar el video con la nueva fuente
        exerciseVideo.style.display = 'block';
        exerciseVideo.play(); // Reproducir automáticamente
        trainerSpeech.textContent = `¡Vamos con ${exerciseName}! ¡Tú puedes!`;

        // Deshabilitar botones de ejercicio
        document.querySelectorAll('.exercise-window button').forEach(button => {
            button.disabled = true;
            button.style.opacity = '0.5';
        });

        // Iniciar temporizador
        let timeLeft = 60;
        timerDisplay.textContent = '1:00';
        setProgress(0);

        const interval = setInterval(() => {
            timeLeft--;
            const minutes = Math.floor(timeLeft / 60);
            const seconds = timeLeft % 60;
            timerDisplay.textContent = `${minutes}:${seconds < 10 ? '0' : ''}${seconds}`;
            setProgress((60 - timeLeft) / 60 * 100);

            if (timeLeft <= 0) {
                clearInterval(interval);
                timerDisplay.textContent = '¡Listo!';
                trainerSpeech.textContent = '¡Bien hecho, ganaste 100 monedas!';
                fetch('/complete_exercise', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                    body: `exercise_type=${exerciseName}`
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        updateMonedas();
                        alert('¡Ejercicio completado! Has ganado 100 monedas.');
                        exerciseVideoContainer.style.display = 'none';
                        exerciseVideo.style.display = 'none';
                        exerciseVideoSource.src = ''; // Limpiar fuente
                        exerciseContent.style.display = 'block';
                        document.querySelectorAll('.exercise-window button').forEach(button => {
                            button.disabled = false;
                            button.style.opacity = '1';
                        });
                    } else {
                        alert('Error: ' + data.message);
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert('Error al procesar el ejercicio.');
                });
            }
        }, 1000);

        // Botón Finalizar
        finishButton.onclick = () => {
            clearInterval(interval);
            exerciseVideoContainer.style.display = 'none';
            exerciseVideo.style.display = 'none';
            exerciseVideoSource.src = ''; // Limpiar fuente
            exerciseVideo.pause(); // Pausar video
            exerciseContent.style.display = 'block';
            timerDisplay.textContent = '1:00';
            setProgress(0);
            trainerSpeech.textContent = '¡Vamos a ponernos fuertes! Elige un ejercicio y comienza lo bueno.';
            document.querySelectorAll('.exercise-window button').forEach(button => {
                button.disabled = false;
                button.style.opacity = '1';
            });
        };
    };
});