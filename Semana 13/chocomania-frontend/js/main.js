/* ChocoManía — página de inicio (Pedidos Especiales):
   grilla de servicios y formulario de cotización. */

(function () {
  const SERVICIOS = [
    {
      nombre: "Chocolates personalizados",
      descripcion: "Tus chocolates con nombre, mensaje, logo o diseño a elección. Ideales para regalos y recuerdos de evento.",
      icon: '<path d="M12 2c2.6 2.6 2.6 6.2 0 8.8-2.6-2.6-2.6-6.2 0-8.8Z"/><path d="M12 10.6c3.6 0 6.5 2.8 6.5 6.5H5.5c0-3.7 2.9-6.5 6.5-6.5Z"/>',
      imagen: "img/servicio-personalizados.jpg",
    },
    {
      nombre: "Cócteles de dulces",
      descripcion: "Mesas y bandejas de mini postres, trufas y bocados de chocolate para acompañar tu celebración.",
      icon: '<circle cx="12" cy="12" r="8.5"/><path d="M9 12h6M12 9v6"/>',
      imagen: "img/servicio-cocteles.jpg",
    },
    {
      nombre: "Delivery",
      descripcion: "Llevamos tu pedido hasta la puerta. Coordinamos horario y comuna al confirmar tu cotización.",
      icon: '<path d="M3 7h11v8H3zM14 10h4l3 3v2h-7z"/><circle cx="7" cy="17" r="1.6"/><circle cx="17.5" cy="17" r="1.6"/>',
      imagen: "img/servicio-delivery.webp",
    },
    {
      nombre: "Tortas por encargo",
      descripcion: "Tortas a medida en sabor, tamaño y decoración, con mensaje y color a elección.",
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
      nombre: "Talleres de chocolatería",
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
    form.addEventListener("submit", (event) => {
      event.preventDefault();
      if (!form.checkValidity()) {
        form.reportValidity();
        return;
      }
      msg.style.display = "block";
      msg.textContent = "¡Gracias! Recibimos tu solicitud y te contactaremos pronto para enviarte la cotización.";
      form.reset();
    });
  }

  document.addEventListener("DOMContentLoaded", () => {
    renderServicios();
    initQuoteForm();
  });
})();
