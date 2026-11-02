/* ChocoManía — página de carrito: listado editable, resumen con cupón,
   método de entrega/pago y confirmación de pedido (todo en el cliente,
   no hay backend de pagos real). */

(function () {
  const CUPONES = {
    CHOCO10: { tipo: "porcentaje", valor: 0.1, etiqueta: "10% de descuento" },
    BIENVENIDO: { tipo: "fijo", valor: 2000, etiqueta: "$2.000 de descuento" },
  };

  let cuponAplicado = null;

  function buildMedia(item) {
    const wrap = document.createElement("div");
    wrap.className = "cart-item__media";
    if (item.imagen) {
      const img = document.createElement("img");
      img.src = item.imagen;
      img.alt = item.nombre;
      img.addEventListener("error", () => img.remove());
      wrap.appendChild(img);
    }
    return wrap;
  }

  function buildCartItem(item) {
    const row = document.createElement("div");
    row.className = "cart-item";

    const info = document.createElement("div");
    info.className = "cart-item__info";
    const nombre = document.createElement("div");
    nombre.className = "cart-item__name";
    nombre.textContent = item.nombre;
    const unit = document.createElement("div");
    unit.className = "cart-item__unit";
    unit.textContent = `${window.ChocoAPI.formatCLP(item.precio)} c/u`;
    const quitar = document.createElement("button");
    quitar.type = "button";
    quitar.className = "cart-item__remove";
    quitar.textContent = "Quitar";
    quitar.addEventListener("click", () => window.ChocoCart.removeItem(item.id));
    info.append(nombre, unit, quitar);

    const qty = document.createElement("div");
    qty.className = "qty-control";
    const dec = document.createElement("button");
    dec.type = "button";
    dec.textContent = "−";
    dec.setAttribute("aria-label", `Quitar una unidad de ${item.nombre}`);
    dec.addEventListener("click", () => window.ChocoCart.setQty(item.id, item.cantidad - 1));
    const span = document.createElement("span");
    span.textContent = item.cantidad;
    const inc = document.createElement("button");
    inc.type = "button";
    inc.textContent = "+";
    inc.setAttribute("aria-label", `Agregar una unidad de ${item.nombre}`);
    inc.addEventListener("click", () => window.ChocoCart.setQty(item.id, item.cantidad + 1));
    qty.append(dec, span, inc);

    const subtotal = document.createElement("div");
    subtotal.className = "cart-item__subtotal";
    subtotal.textContent = window.ChocoAPI.formatCLP(item.precio * item.cantidad);

    row.append(buildMedia(item), info, qty, subtotal);
    return row;
  }

  function renderCart() {
    const cont = document.getElementById("cartItems");
    const emptyMsg = document.getElementById("cartEmptyMsg");
    const contactPanel = document.getElementById("contactPanel");
    const paymentPanel = document.getElementById("paymentPanel");
    const items = window.ChocoCart.getItems();

    cont.innerHTML = "";
    const vacio = items.length === 0;
    emptyMsg.hidden = !vacio;
    contactPanel.style.display = vacio ? "none" : "";
    paymentPanel.style.display = vacio ? "none" : "";

    items.forEach((item) => cont.appendChild(buildCartItem(item)));
    renderSummary(items);
  }

  function calcularEnvio() {
    const metodo = document.getElementById("metodoEntrega").value;
    return metodo === "tienda" ? "Gratis" : "Por calcular";
  }

  function renderSummary(items) {
    const subtotal = window.ChocoCart.subtotal(items);
    let descuento = 0;
    if (cuponAplicado) {
      descuento =
        cuponAplicado.tipo === "porcentaje"
          ? Math.round(subtotal * cuponAplicado.valor)
          : Math.min(cuponAplicado.valor, subtotal);
    }
    const total = Math.max(0, subtotal - descuento);

    document.getElementById("sumSubtotal").textContent = window.ChocoAPI.formatCLP(subtotal);
    document.getElementById("sumEnvio").textContent = calcularEnvio();
    document.getElementById("sumTotal").textContent = window.ChocoAPI.formatCLP(total);

    const discountRow = document.getElementById("sumDiscountRow");
    if (descuento > 0) {
      discountRow.hidden = false;
      document.getElementById("sumDiscount").textContent = "-" + window.ChocoAPI.formatCLP(descuento);
    } else {
      discountRow.hidden = true;
    }
  }

  function initCupon() {
    const input = document.getElementById("cupon");
    const msg = document.getElementById("cuponMsg");
    document.getElementById("aplicarCupon").addEventListener("click", () => {
      const codigo = input.value.trim().toUpperCase();
      const cupon = CUPONES[codigo];
      if (!codigo) {
        msg.textContent = "Ingresa un código de descuento.";
        cuponAplicado = null;
      } else if (cupon) {
        cuponAplicado = cupon;
        msg.textContent = `Código aplicado: ${cupon.etiqueta}.`;
      } else {
        cuponAplicado = null;
        msg.textContent = "Ese código no es válido.";
      }
      renderSummary(window.ChocoCart.getItems());
    });
  }

  function initDeliveryGroup() {
    const buttons = document.querySelectorAll("#deliveryGroup .option-btn");
    const hidden = document.getElementById("metodoEntrega");
    const fields = document.getElementById("deliveryFields");
    const inputs = fields.querySelectorAll("input");

    buttons.forEach((btn) => {
      btn.addEventListener("click", () => {
        buttons.forEach((b) => b.setAttribute("aria-pressed", String(b === btn)));
        hidden.value = btn.dataset.delivery;
        const esDomicilio = btn.dataset.delivery === "domicilio";
        fields.style.display = esDomicilio ? "" : "none";
        inputs.forEach((input) => {
          if (input.id === "depto") return;
          input.required = esDomicilio;
        });
        renderSummary(window.ChocoCart.getItems());
      });
    });
  }

  function initPaymentToggle() {
    const cardFields = document.getElementById("cardFields");
    const radios = document.querySelectorAll('input[name="metodoPago"]');
    function sync() {
      const seleccionado = document.querySelector('input[name="metodoPago"]:checked').value;
      cardFields.style.display = seleccionado === "tarjeta" ? "" : "none";
      cardFields.querySelectorAll("input").forEach((input) => {
        input.required = seleccionado === "tarjeta";
      });
    }
    radios.forEach((r) => r.addEventListener("change", sync));
    sync();
  }

  function initConfirm() {
    const btn = document.getElementById("confirmarBtn");
    const msg = document.getElementById("checkoutMsg");
    btn.addEventListener("click", () => {
      const contactForm = document.getElementById("contactForm");
      const paymentForm = document.getElementById("paymentForm");
      if (window.ChocoCart.getItems().length === 0) return;
      if (!contactForm.reportValidity()) return;
      if (!paymentForm.reportValidity()) return;

      const numeroPedido = "CM-" + Math.floor(100000 + Math.random() * 900000);
      document.getElementById("cartLayout").hidden = true;
      const confirmPanel = document.getElementById("confirmPanel");
      document.getElementById("confirmMsg").textContent =
        `Gracias por tu compra. Tu número de pedido es ${numeroPedido}. Te enviaremos la confirmación a tu correo.`;
      confirmPanel.hidden = false;
      confirmPanel.scrollIntoView({ behavior: "smooth", block: "start" });
      window.ChocoCart.clear();
      msg.style.display = "none";
    });
  }

  document.addEventListener("DOMContentLoaded", () => {
    document.addEventListener("chocomania:cart-updated", renderCart);
    initCupon();
    initDeliveryGroup();
    initPaymentToggle();
    initConfirm();
    renderCart();
  });
})();
