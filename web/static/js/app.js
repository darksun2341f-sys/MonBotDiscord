document.addEventListener('DOMContentLoaded', () => {
  const navButtons = Array.from(document.querySelectorAll('.nav-btn'));
  const sections = Array.from(document.querySelectorAll('.panel-section'));
  const forms = Array.from(document.querySelectorAll('.config-form'));
  const guildSelect = document.getElementById('guildSelect');

  const setActiveSection = (sectionId) => {
    sections.forEach((section) => section.classList.toggle('active', section.id === sectionId));
    navButtons.forEach((button) => button.classList.toggle('active', button.dataset.section === sectionId));
  };

  navButtons.forEach((button) => {
    button.addEventListener('click', () => setActiveSection(button.dataset.section));
  });

  forms.forEach((form) => {
    form.addEventListener('submit', async (event) => {
      event.preventDefault();
      const payload = Object.fromEntries(new FormData(form).entries());
      const section = form.dataset.section;
      const guildId = guildSelect?.value || 'default';
      const response = await fetch(`/api/settings/${guildId}/${section}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      if (response.ok) {
        const button = form.querySelector('button');
        if (button) {
          button.textContent = 'Saved';
          window.setTimeout(() => (button.textContent = 'Save'), 1200);
        }
      }
    });
  });

  if (guildSelect) {
    guildSelect.addEventListener('change', () => {
      window.location.href = `/dashboard?guild=${guildSelect.value}`;
    });
  }

  if (navButtons.length) {
    setActiveSection('overview');
  }
});
