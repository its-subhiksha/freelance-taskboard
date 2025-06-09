document.addEventListener('DOMContentLoaded', function () {
    const collapsibles = document.querySelectorAll('.collapsible');
    collapsibles.forEach(button => {
      button.addEventListener('click', () => {
        const submenu = button.nextElementSibling;
        submenu.classList.toggle('open');
        button.classList.toggle('active');
      });
    });
  });
  