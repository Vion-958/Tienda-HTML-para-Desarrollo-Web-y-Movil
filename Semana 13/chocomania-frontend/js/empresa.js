/* ChocoManía — página Sobre Nosotros: formulario de contacto. */

(function () {
  function initContactForm() {
    const form = document.getElementById("contactUsForm");
    const msg = document.getElementById("contactUsMsg");
    if (!form || !msg) return;
    form.addEventListener("submit", (event) => {
      event.preventDefault();
      if (!form.checkValidity()) {
        form.reportValidity();
        return;
      }
      msg.style.display = "block";
      msg.textContent = "¡Gracias por escribirnos! Te responderemos a la brevedad.";
      form.reset();
    });
  }

  document.addEventListener("DOMContentLoaded", initContactForm);
})();
