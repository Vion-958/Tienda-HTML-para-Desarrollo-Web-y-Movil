// Pedidos Especiales: servicios y formulario de cotizacion.

(function () {
  const SERVICIOS = [
    {
      nombre: "Chocolates personalizados",
      descripcion: "Tus chocolates con nombre, mensaje, logo o dise\u00f1o a elecci\u00f3n. Ideales para regalos y recuerdos de evento.",
      icon: '<path d="M12 2c2.6 2.6 2.6 6.2 0 8.8-2.6-2.6-2.6-6.2 0-8.8Z"/><path d="M12 10.6c3.6 0 6.5 2.8 6.5 6.5H5.5c0-3.7 2.9-6.5 6.5-6.5Z"/>',
      imagen: "img/servicio-personalizados.jpg",
    },
    {
      nombre: "C\u00f3cteles de dulces",
      descripcion: "Mesas y bandejas de mini postres, trufas y bocados de chocolate para acompa\u00f1ar tu celebraci\u00f3n.",
      icon: '<circle cx="12" cy="12" r="8.5"/><path d="M9 12h6M12 9v6"/>',
      imagen: "img/servicio-cocteles.jpg",
    },
    {
      nombre: "Delivery",
      descripcion: "Llevamos tu pedido hasta la puerta. Coordinamos horario y comuna al confirmar tu cotizaci\u00f3n.",
      icon: '<path d="M3 7h11v8H3zM14 10h4l3 3v2h-7z"/><circle cx="7" cy="17" r="1.6"/><circle cx="17.5" cy="17" r="1.6"/>',
      imagen: "img/servicio-delivery.webp",
    },
    {
      nombre: "Tortas por encargo",
      descripcion: "Tortas a medida en sabor, tama\u00f1o y decoraci\u00f3n, con mensaje y color a elecci\u00f3n.",
      icon: '<path d="M4 20h16M5 20v-5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2v5M8 13V9h8v4M11 9V5h2v4"/>',
      imagen: "img/servicio-tortas.jpg",
    },
    {
      nombre: "Regalos corporativos",
      descripcion: "Cajas de chocolate para clientes, equipos y fechas especiales, con tu marca y precio por volumen.",
      icon: '<rect x="4" y="9" width="16" height="11" rx="1.4"/><path d="M4 9V7a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v2M12 5v15"/>',
      imagen: "img/servicio-regalos.png",
    },
    {
      nombre: "Talleres de chocolater\u00eda",
      descripcion: "Aprende a templar, moldear y decorar chocolate junto a nuestro maestro chocolatero.",
      icon: '<path d="M6 3v6a6 6 0 0 0 12 0V3M4 3h16M8 21h8M12 15v6"/>',
      imagen: "img/servicio-talleres.jpg",
    },
  ];

  function renderServicios() {
    const grid = document.getElementById("serviciosGrid");
    if (!grid) return;
    SERVICIOS.forEach((servicio) => {
      const card = document.createElement("article");
      card.className = "service-card";

      const icon = document.createElement("div");
      icon.className = "service-card__icon";
      if (servicio.imagen) {
        icon.innerHTML = `<img src="${servicio.imagen}" alt="" style="width:100%; height:100%; object-fit:cover; border-radius:50%;">`;
      } else {
        icon.setAttribute("aria-hidden", "true");
        icon.innerHTML = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">${servicio.icon}</svg>`;
      }

      const titulo = document.createElement("h3");
      titulo.textContent = servicio.nombre;
      titulo.style.margin = "0";
      titulo.style.fontSize = "18px";

      const desc = document.createElement("p");
      desc.textContent = servicio.descripcion;

      const boton = document.createElement("a");
      boton.className = "btn btn--accent btn--pill";
      boton.href = "#cotizar";
      boton.textContent = "Cotizar";
      boton.addEventListener("click", () => {
        const select = document.getElementById("tipo");
        if (select) {
          const opciones = Array.from(select.options);
          const match = opciones.find((o) => o.value === servicio.nombre);
          if (match) select.value = servicio.nombre;
        }
      });

      card.append(icon, titulo, desc, boton);
      grid.appendChild(card);
    });
  }

  function initQuoteForm() {
    const form = document.getElementById("quoteForm");
    const msg = document.getElementById("quoteMsg");
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
        tipo: "cotizacion",
        nombre: form.nombre.value,
        email: form.correo.value,
        telefono: form.telefono.value,
        asunto: form.tipo.value,
        fecha_requerida: form.fecha.value,
        cantidad: form.cantidad.value,
        mensaje: form.detalles.value,
      });
      if (boton) boton.disabled = false;
      msg.style.display = "block";
      if (r.status === 201) {
        msg.style.color = "";
        msg.textContent = `\u00a1Gracias! Recibimos tu solicitud N\u00b0 ${r.data.id}. Te enviaremos la cotizaci\u00f3n pronto.`;
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

  document.addEventListener("DOMContentLoaded", () => {
    renderServicios();
    initQuoteForm();
  });
})();
