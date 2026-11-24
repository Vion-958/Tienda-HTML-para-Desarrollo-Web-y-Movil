// Sobre Nosotros: formulario de contacto.

(function () {
  function initContactForm() {
    const form = document.getElementById("contactUsForm");
    const msg = document.getElementById("contactUsMsg");
    if (!form || !msg) return;
    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      if (!form.checkValidity()) {
        form.reportValidity();
        return;
      }
      const boton = form.querySelector('button[type="submit"]');
      if (boton) boton.disabled = true;
      const r = await window.ChocoAPI.enviarSolicitud({
        tipo: "contacto",
        email: form.emailContacto.value,
        asunto: form.motivo.value,
        mensaje: form.comentarios.value,
      });
      if (boton) boton.disabled = false;
      msg.style.display = "block";
      if (r.status === 201) {
        msg.style.color = "";
        msg.textContent = `\u00a1Gracias por escribirnos! Tu mensaje N\u00b0 ${r.data.id} lleg\u00f3 a nuestro equipo.`;
        form.reset();
      } else {
        msg.style.color = "var(--danger)";
        const d = r.data && r.data.detail;
        msg.textContent = r.status === 429 ? "Enviaste varias solicitudes seguidas. Espera un minuto." :
          Array.isArray(d) && d[0] ? d[0].msg.replace("Value error, ", "") :
          typeof d === "string" ? d : "No pudimos enviar tu solicitud. Intenta de nuevo.";
      }
    });
  }

  document.addEventListener("DOMContentLoaded", initContactForm);
})();
