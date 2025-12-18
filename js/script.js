(function() {
  const navLinks = document.querySelectorAll('nav a');
  const current = window.location.pathname.split('/').pop() || 'index.html';
  navLinks.forEach(link => {
    const href = link.getAttribute('href');
    if (href === current || (current === '' && href === 'index.html')) {
      link.classList.add('active');
    }
  });

  const menuToggle = document.querySelector('.menu-toggle');
  const navList = document.querySelector('nav ul');

  if (menuToggle && navList) {
    menuToggle.addEventListener('click', () => {
      navList.classList.toggle('open');
    });

    navLinks.forEach(link => {
      link.addEventListener('click', () => navList.classList.remove('open'));
    });
  }

  const yearEl = document.getElementById('year');
  if (yearEl) {
    yearEl.textContent = new Date().getFullYear();
  }

  const contactForm = document.querySelector('[data-contact-form]');
  const alertBox = document.querySelector('[data-alert]');

  if (contactForm && alertBox) {
    contactForm.addEventListener('submit', event => {
      event.preventDefault();
      const formData = new FormData(contactForm);
      const name = formData.get('nom');
      alertBox.textContent = `Merci ${name ? name + ',' : ''} nous revenons vers vous dans les plus brefs délais.`;
      alertBox.hidden = false;
      contactForm.reset();
    });
  }
})();
