// Carrito y checkout: el total lo calcula el servidor.

(function () {
  const ENVIO = 3000;
  const ENVIO_GRATIS_DESDE = 30000;
  let usuario = null;
  let perfil = {};

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
    dec.textContent = "\u2212";
    dec.setAttribute("aria-label", `Quitar una unidad de ${item.nombre}`);
    dec.addEventListener("click", () => window.ChocoCart.setQty(item.id, item.cantidad - 1));
    const span = document.createElement("span");
    span.textContent = item.cantidad;
    const inc = document.createElement("button");
    inc.type = "button";
    inc.textContent = "+";
    inc.setAttribute("aria-label", `Agregar una unidad de ${item.nombre}`);
    inc.disabled = typeof item.stock === "number" && item.cantidad >= item.stock;
    if (inc.disabled) inc.title = `Quedan ${item.stock}`;
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
    const sinSesion = !usuario;
    document.getElementById("loginPanel").hidden = vacio || !sinSesion;
    contactPanel.style.display = vacio || sinSesion ? "none" : "";
    paymentPanel.style.display = vacio || sinSesion ? "none" : "";

    items.forEach((item) => cont.appendChild(buildCartItem(item)));
    renderSummary(items);
  }

  function esDelivery() {
    return document.getElementById("metodoEntrega").value === "domicilio";
  }

  function costoEnvio(subtotal) {
    return esDelivery() && subtotal < ENVIO_GRATIS_DESDE ? ENVIO : 0;
  }

  function renderSummary(items) {
    const subtotal = window.ChocoCart.subtotal(items);
    const envio = costoEnvio(subtotal);
    const fmt = window.ChocoAPI.formatCLP;
    document.getElementById("sumSubtotal").textContent = fmt(subtotal);
    document.getElementById("sumEnvio").textContent = envio ? fmt(envio) : "Gratis";
    document.getElementById("sumTotal").textContent = fmt(subtotal + envio);
  }

  function initDeliveryGroup() {
    const buttons = document.querySelectorAll("#deliveryGroup .option-btn");
    const hidden = document.getElementById("metodoEntrega");
    const fields = document.getElementById("deliveryFields");
    buttons.forEach((btn) => {
      btn.addEventListener("click", () => {
        buttons.forEach((b) => b.setAttribute("aria-pressed", String(b === btn)));
        hidden.value = btn.dataset.delivery;
        fields.style.display = esDelivery() ? "" : "none";
        ["direccion", "comuna"].forEach((id) => {
          document.getElementById(id).required = esDelivery();
        });
        renderSummary(window.ChocoCart.getItems());
      });
    });
  }

  function initPaymentToggle() {
    const sync = () => {
      const metodo = document.querySelector('input[name="metodoPago"]:checked').value;
      document.getElementById("cardFields").hidden = metodo !== "tarjeta";
      document.getElementById("transferFields").hidden = metodo !== "transferencia";
    };
    document.querySelectorAll('input[name="metodoPago"]').forEach((r) => r.addEventListener("change", sync));
    sync();
  }

  async function precargarPerfil() {
    const r = await window.ChocoAPI.miPerfil();
    if (r.status !== 200 || !r.data) return;
    const c = r.data.client;
    perfil = c;
    const partes = (c.nombre || "").split(" ");
    const poner = (id, v) => {
      const el = document.getElementById(id);
      if (el && !el.value) el.value = v || "";
    };
    poner("nombre", partes.shift());
    poner("apellido", partes.join(" "));
    poner("correo", c.email);
    poner("telefono", c.telefono);
    poner("direccion", c.direccion);
    poner("comuna", c.comuna);
  }

  function mensaje(texto, error = true) {
    const msg = document.getElementById("checkoutMsg");
    msg.textContent = texto;
    msg.style.display = texto ? "" : "none";
    msg.style.color = error ? "var(--danger)" : "";
  }

  function detalle(r, porDefecto) {
    const d = r.data && r.data.detail;
    if (typeof d === "string") return d;
    if (d && Array.isArray(d.productos) && d.productos.some((x) => x && x.disponible !== undefined)) {
      // Sin stock: nombra cada producto y cuantos quedan.
      const items = window.ChocoCart.getItems();
      const nombre = (id) => (items.find((i) => String(i.id) === String(id)) || { nombre: id }).nombre;
      return "No hay stock suficiente: " +
        d.productos.map((x) => `${nombre(x.producto_id)} (quedan ${x.disponible})`).join(", ") +
        ". Ajusta la cantidad en tu carrito.";
    }
    if (d && typeof d.mensaje === "string") return d.mensaje;
    if (Array.isArray(d) && d[0] && d[0].msg) return d[0].msg.replace("Value error, ", "");
    return porDefecto;
  }

  function mostrarTransferencia(pedido, instrucciones) {
    document.getElementById("cartLayout").hidden = true;
    const panel = document.getElementById("confirmPanel");
    document.getElementById("confirmMsg").textContent =
      `Tu pedido #${pedido.id} por ${window.ChocoAPI.formatCLP(pedido.total)} qued\u00f3 pendiente de pago. ` +
      "Transfiere a esta cuenta usando la referencia indicada:";
    const dl = document.getElementById("transferData");
    dl.innerHTML = "";
    [["Banco", instrucciones.banco], ["Tipo", instrucciones.tipo], ["N\u00famero", instrucciones.numero],
      ["RUT", instrucciones.rut], ["Titular", instrucciones.titular],
      ["Monto", window.ChocoAPI.formatCLP(instrucciones.monto)], ["Referencia", instrucciones.referencia]]
      .forEach(([k, v]) => {
        const dt = document.createElement("dt");
        dt.textContent = k;
        const dd = document.createElement("dd");
        dd.textContent = v;
        dl.append(dt, dd);
      });
    dl.hidden = false;
    panel.hidden = false;
    panel.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  async function confirmar() {
    const items = window.ChocoCart.getItems();
    if (!items.length) return;
    if (!document.getElementById("contactForm").reportValidity()) return;
    if (!document.getElementById("paymentForm").reportValidity()) return;

    const btn = document.getElementById("confirmarBtn");
    const valor = (id) => document.getElementById(id).value.trim();
    const metodo = document.querySelector('input[name="metodoPago"]:checked').value;
    btn.disabled = true;
    mensaje("Procesando\u2026", false);

    try {
      // Datos de contacto -> clients.
      const direccion = [valor("direccion"), valor("depto")].filter(Boolean).join(", ");
      const guardado = await window.ChocoAPI.guardarPerfil({
        nombre: `${valor("nombre")} ${valor("apellido")}`.trim(),
        email: valor("correo"),
        telefono: valor("telefono"),
        // Con retiro se conserva la direccion guardada.
        direccion: esDelivery() ? direccion : perfil.direccion || "",
        comuna: esDelivery() ? valor("comuna") : perfil.comuna || "",
      });
      if (guardado.status !== 200) {
        return mensaje(detalle(guardado, "Revisa tus datos de contacto."));
      }
      perfil = guardado.data.client || perfil;

      // Pedido -> orders.
      const r = await window.ChocoAPI.crearPedido({
        items: items.map((i) => ({ producto_id: String(i.id), cantidad: i.cantidad })),
        entrega: esDelivery() ? "delivery" : "retiro",
        direccion: esDelivery() ? direccion : "",
        comuna: esDelivery() ? valor("comuna") : "",
        metodo_pago: metodo,
        nota: valor("notas").slice(0, 200),
      });
      if (r.status === 401) return mensaje("Tu sesi\u00f3n expir\u00f3. Vuelve a iniciar sesi\u00f3n.");
      if (r.status !== 201) return mensaje(detalle(r, "No pudimos crear el pedido. Intenta de nuevo."));
      const pedido = r.data.order;
      window.ChocoCart.clear();

      // Pago -> payments.
      const p = await window.ChocoAPI.iniciarPago(pedido.id);
      if (p.status !== 201 && p.status !== 200) {
        return mensaje(`Pedido #${pedido.id} creado, pero el pago no se pudo iniciar. Puedes pagarlo desde Mi cuenta.`);
      }
      if (p.data.redirect_url) {
        window.location.href = p.data.redirect_url;
        return;
      }
      mensaje("");
      mostrarTransferencia(pedido, p.data.instrucciones);
    } finally {
      btn.disabled = false;
    }
  }

  document.addEventListener("DOMContentLoaded", async () => {
    document.addEventListener("chocomania:cart-updated", renderCart);
    initDeliveryGroup();
    initPaymentToggle();
    document.getElementById("confirmarBtn").addEventListener("click", confirmar);
    usuario = await window.ChocoAPI.me();
    renderCart();
    if (usuario) precargarPerfil();
  });
})();
