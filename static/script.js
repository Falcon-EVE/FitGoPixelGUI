document.addEventListener("DOMContentLoaded", function () {
  const menu = document.querySelector('.menu');
  const openBtn = document.querySelector('.toggle__menu-open');
  const closeBtn = document.querySelector('.toggle__menu-close');
  // Asignamos la acción de clic en los botones
  openBtn.addEventListener('click', toggleMenu);
  closeBtn.addEventListener('click', toggleMenu);
  // Aseguramos que el menú esté oculto al principio
  menu.style.bottom = '-10%';
  menu.style.opacity = '0';

  // Función para alternar el estado del menú
  function toggleMenu() {
    if (menu.style.bottom === '-10%') {
      // Mostrar el menú
      menu.style.bottom = '0';
      menu.style.opacity = '1';
      openBtn.style.opacity = '0';
      closeBtn.style.opacity = '1';
      closeBtn.style.display = 'block'; // Mostrar el botón de cerrar
    } else {
      // Ocultar el menú
      menu.style.bottom = '-10%';
      menu.style.opacity = '0';
      openBtn.style.opacity = '1';
      closeBtn.style.opacity = '0';
      closeBtn.style.display = 'none'; // Ocultar el botón de cerrar
    }
  }


});
