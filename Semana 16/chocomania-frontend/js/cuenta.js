// Mi cuenta: sesion, perfil, pedidos y administracion. El servidor valida los permisos.

(function () {
  const $ = (id) => document.getElementById(id);
  const API = () => window.ChocoAPI;

  const ESTADOS = {
    pendiente_pago: "Pendiente de pago",
    pagado: "Pagado",
    en_preparacion: "En preparaci\u00f3n",
    listo_retiro: "Listo para retiro",
    despachado: "Despachado",
    entregado: "Entregado",
    cancelado: "Cancelado",
  };
  const PAGOS = { pendiente: "Pendiente", aprobado: "Aprobado", rechazado: "Rechazado", anulado: "Anulado" };
  const SIGUIENTE = {
    pagado: [["en_preparacion", "Preparar"]],
    en_preparacion: [["listo_retiro", "Listo retiro"], ["despachado", "Despachar"]],
    listo_retiro: [["entregado", "Entregado"]],
    despachado: [["entregado", "Entregado"]],
  };

  const MAX_IMAGENES = 5;
  const MAX_BYTES_IMAGEN = 2 * 1024 * 1024;
  const TIPOS_IMAGEN = ["image/jpeg", "image/png", "image/webp"];

  const CAMPOS_PEDIDO = `id estado entrega comuna total creado metodoPago
    items { nombre cantidad productoId producto { imagen } }
    pago { id estado metodo }`;

  let usuarioActual = null;
  let imagenesSeleccionadas = [];
  let editandoId = null;

  // --- utilidades

  function show(seccion) {
    $("accountLoading").hidden = true;
    ["login", "register", "account"].forEach((s) => {
      $(`${s}Section`).hidden = s !== seccion;
    });
  }

  function setMsg(el, texto, tipo) {
    el.textContent = texto;
    el.hidden = !texto;
    el.classList.toggle("account-msg--error", tipo === "error");
    el.classList.toggle("account-msg--ok", tipo === "ok");
  }

  function cell(texto) {
    const td = document.createElement("td");
    td.textContent = texto;
    return td;
  }

  function boton(texto, clase, datos) {
    const b = document.createElement("button");
    b.type = "button";
    b.className = `btn btn--sm ${clase}`;
    b.textContent = texto;
    Object.entries(datos).forEach(([k, v]) => (b.dataset[k] = v));
    return b;
  }

  function etiquetaEstado(estado) {
    const td = document.createElement("td");
    const span = document.createElement("span");
    span.className = `order-status order-status--${estado}`;
    span.textContent = ESTADOS[estado] || estado;
    td.appendChild(span);
    return td;
  }

  function detalle(r, porDefecto) {
    const d = r.data && r.data.detail;
    if (typeof d === "string") return d;
    if (d && typeof d.mensaje === "string") return d.mensaje;
    if (Array.isArray(d) && d[0] && d[0].msg) return d[0].msg.replace("Value error, ", "");
    return porDefecto;
  }

  function esAdmin(u) {
    return Boolean(u && u.roles.includes("admin"));
  }

  function fecha(texto) {
    return (texto || "").slice(0, 10).split("-").reverse().join("-");
  }

  function productosTexto(items) {
    return items.map((i) => `${i.cantidad} x ${i.nombre}`).join(", ");
  }

  function actualizarLinkCuenta(u) {
    document.querySelectorAll("[data-account-link]").forEach((a) => {
      a.textContent = u ? `Hola, ${u.username}` : "Mi cuenta";
    });
  }

  async function sesionExpirada() {
    await mostrarLogin("Tu sesi\u00f3n expir\u00f3. Vuelve a iniciar sesi\u00f3n.");
  }

  // --- mis pedidos (GraphQL)

  let ultimosPedidos = [];

  async function cargarPedidos() {
    const tabla = $("ordersTable");
    const msg = $("ordersMsg");
    const r = await API().graphql(`query { misPedidos(tamano: 20) { total pedidos { ${CAMPOS_PEDIDO} } } }`);
    const tbody = tabla.querySelector("tbody");
    tbody.innerHTML = "";
    if (r.status === 401) return sesionExpirada();
    if (!r.data || !r.data.misPedidos) {
      tabla.hidden = true;
      msg.hidden = false;
      msg.textContent = "No pudimos cargar tus pedidos. Intenta de nuevo en unos minutos.";
      return;
    }
    const pedidos = r.data.misPedidos.pedidos;
    ultimosPedidos = pedidos;
    if (!pedidos.length) {
      tabla.hidden = true;
      msg.hidden = false;
      msg.textContent = "A\u00fan no tienes pedidos.";
      return;
    }
    pedidos.forEach((p) => {
      const tr = document.createElement("tr");
      tr.dataset.orderId = p.id;
      const acciones = document.createElement("td");
      acciones.className = "account-actions";
      const pagoVivo = p.pago && p.pago.estado !== "rechazado";
      if (p.estado === "pendiente_pago") {
        if (!pagoVivo || p.metodoPago === "tarjeta") {
          acciones.appendChild(boton("Pagar", "btn--accent", { payId: p.id }));
        }
        acciones.appendChild(boton("Cancelar", "btn--ghost", { cancelId: p.id }));
      }
      tr.append(
        cell(`#${p.id}`),
        cell(fecha(p.creado)),
        cell(productosTexto(p.items)),
        cell(p.entrega === "delivery" ? `Delivery (${p.comuna})` : "Retiro"),
        etiquetaEstado(p.estado),
        cell(p.pago ? `${PAGOS[p.pago.estado] || p.pago.estado} (${p.pago.metodo})` : "\u2014"),
        cell(API().formatCLP(p.total)),
        acciones
      );
      if (p.estado === "cancelado") tr.classList.add("is-cancelled");
      tbody.appendChild(tr);
    });
    if (r.errors.length) {
      msg.hidden = false;
      msg.textContent = "Algunos datos no se pudieron cargar (pago o im\u00e1genes). Se muestran los disponibles.";
    } else {
      msg.hidden = true;
    }
    tabla.hidden = false;
  }

  async function pagar(id, btn) {
    btn.disabled = true;
    const r = await API().iniciarPago(id);
    btn.disabled = false;
    const msg = $("orderActionMsg");
    if ((r.status === 201 || r.status === 200) && r.data.redirect_url) {
      window.location.href = r.data.redirect_url;
    } else if (r.status === 201 || r.status === 200) {
      const i = r.data.instrucciones;
      setMsg(msg, i ? `Transfiere ${API().formatCLP(i.monto)} a ${i.banco}, cuenta ${i.numero}, referencia ${i.referencia}.` :
        "El pago ya fue registrado.", "ok");
    } else if (r.status === 401) {
      sesionExpirada();
    } else {
      setMsg(msg, detalle(r, "No se pudo iniciar el pago."), "error");
    }
  }

  async function cancelar(id, btn) {
    if (!window.confirm(`\u00bfCancelar el pedido #${id}? El stock vuelve a la tienda.`)) return;
    btn.disabled = true;
    const r = await API().cancelarPedido(id);
    btn.disabled = false;
    const msg = $("orderActionMsg");
    if (r.status === 200) {
      setMsg(msg, `Pedido #${id} cancelado.`, "ok");
      await cargarPedidos();
      if (esAdmin(usuarioActual)) await Promise.all([cargarPedidosAdmin(), cargarProductos()]);
    } else if (r.status === 401) {
      sesionExpirada();
    } else {
      setMsg(msg, detalle(r, "No se pudo cancelar el pedido."), "error");
      await cargarPedidos();
    }
  }

  // El mensaje usa el estado del servidor, no el parametro de la URL.
  function avisoRetornoPago(pedidoId) {
    if (!pedidoId) return;
    const p = ultimosPedidos.find((x) => String(x.id) === pedidoId);
    const pago = p && p.pago ? p.pago.estado : "";
    if (pago === "aprobado") {
      setMsg($("orderActionMsg"), `Pago aprobado. Tu pedido #${pedidoId} ya est\u00e1 pagado.`, "ok");
    } else if (pago === "rechazado") {
      setMsg($("orderActionMsg"), `El pago del pedido #${pedidoId} fue rechazado. Puedes intentarlo de nuevo.`, "error");
    } else if (pago === "anulado") {
      setMsg($("orderActionMsg"), `El pedido #${pedidoId} estaba cancelado, as\u00ed que el pago se anul\u00f3. Si se hizo un cargo, escr\u00edbenos para devolverlo.`, "error");
    } else {
      setMsg($("orderActionMsg"), `Estamos confirmando el pago del pedido #${pedidoId}. Recarga en unos segundos.`, "ok");
    }
  }

  // --- perfil (clients)

  async function cargarPerfil() {
    const r = await API().miPerfil();
    if (r.status !== 200) return;
    const c = r.data.client;
    $("pNombre").value = c.nombre;
    $("pCorreo").value = c.email;
    $("pTelefono").value = c.telefono;
    $("pComuna").value = c.comuna;
    $("pDireccion").value = c.direccion;
  }

  async function guardarPerfil(e) {
    e.preventDefault();
    setMsg($("profileMsg"), "");
    if (!$("profileForm").reportValidity()) return;
    $("profileBtn").disabled = true;
    const r = await API().guardarPerfil({
      nombre: $("pNombre").value.trim(),
      email: $("pCorreo").value.trim(),
      telefono: $("pTelefono").value.trim(),
      comuna: $("pComuna").value.trim(),
      direccion: $("pDireccion").value.trim(),
    });
    $("profileBtn").disabled = false;
    setMsg($("profileMsg"), r.status === 200 ? "Datos guardados." : detalle(r, "No se pudieron guardar."),
      r.status === 200 ? "ok" : "error");
  }

  // --- admin: pedidos

  async function cargarPedidosAdmin() {
    const estado = $("adminEstado").value;
    const r = await API().graphql(
      `query($estado: String) { pedidosAdmin(estado: $estado, tamano: 20) { total pedidos {
        ${CAMPOS_PEDIDO} cliente { nombre email telefono } } } }`,
      { estado: estado || null }
    );
    const tbody = $("adminOrdersTable").querySelector("tbody");
    tbody.innerHTML = "";
    if (!r.data || !r.data.pedidosAdmin) {
      setMsg($("adminOrdersMsg"), "No se pudieron cargar los pedidos.", "error");
      return;
    }
    r.data.pedidosAdmin.pedidos.forEach((p) => {
      const tr = document.createElement("tr");
      tr.dataset.adminOrderId = p.id;
      const cliente = document.createElement("td");
      cliente.textContent = p.cliente ? p.cliente.nombre : "\u2014";
      if (p.cliente) {
        const small = document.createElement("small");
        small.style.display = "block";
        small.textContent = p.cliente.email;
        cliente.appendChild(small);
      }
      const acciones = document.createElement("td");
      acciones.className = "account-actions";
      (SIGUIENTE[p.estado] || [])
        .filter(([estado]) => !(estado === "listo_retiro" && p.entrega !== "retiro") &&
          !(estado === "despachado" && p.entrega !== "delivery"))
        .forEach(([estado, texto]) => acciones.appendChild(boton(texto, "btn--accent", { setEstado: estado, orderId: p.id })));
      if (p.estado === "pendiente_pago" && p.pago && p.pago.metodo === "transferencia" && p.pago.estado === "pendiente") {
        acciones.appendChild(boton("Confirmar transferencia", "btn--accent", { confirmPago: p.pago.id }));
      }
      if (["pendiente_pago", "pagado", "en_preparacion"].includes(p.estado)) {
        acciones.appendChild(boton("Anular", "btn--ghost", { setEstado: "cancelado", orderId: p.id }));
      }
      tr.append(
        cell(`#${p.id}`),
        cliente,
        cell(productosTexto(p.items)),
        cell(p.entrega === "delivery" ? `Delivery (${p.comuna})` : "Retiro"),
        etiquetaEstado(p.estado),
        cell(p.pago ? `${PAGOS[p.pago.estado] || p.pago.estado} (${p.pago.metodo})` : "\u2014"),
        cell(API().formatCLP(p.total)),
        acciones
      );
      if (p.estado === "cancelado") tr.classList.add("is-cancelled");
      tbody.appendChild(tr);
    });
  }

  async function cambiarEstado(id, estado, btn) {
    if (estado === "cancelado" && !window.confirm(`\u00bfAnular el pedido #${id}? El stock vuelve al cat\u00e1logo.`)) return;
    btn.disabled = true;
    const r = await API().cambiarEstado(id, estado);
    btn.disabled = false;
    const ok = r.status === 200;
    setMsg($("adminOrdersMsg"), ok ? `Pedido #${id}: ${ESTADOS[estado]}.` : detalle(r, "No se pudo cambiar el estado."),
      ok ? "ok" : "error");
    await cargarPedidosAdmin();
    if (estado === "cancelado") await cargarProductos();
  }

  async function confirmarPago(pagoId, btn) {
    btn.disabled = true;
    const r = await API().confirmarTransferencia(pagoId);
    btn.disabled = false;
    setMsg($("adminOrdersMsg"), r.status === 200 ? "Transferencia confirmada: el pedido qued\u00f3 pagado." :
      detalle(r, "No se pudo confirmar."), r.status === 200 ? "ok" : "error");
    await Promise.all([cargarPedidosAdmin(), cargarPedidos()]);
  }

  // --- admin: solicitudes

  async function cargarSolicitudes() {
    const r = await API().adminSolicitudes();
    const tbody = $("adminRequestsTable").querySelector("tbody");
    tbody.innerHTML = "";
    if (r.status !== 200) {
      setMsg($("adminRequestsMsg"), "No se pudieron cargar las solicitudes.", "error");
      return;
    }
    if (!r.data.solicitudes.length) {
      setMsg($("adminRequestsMsg"), "No hay solicitudes.", null);
      return;
    }
    r.data.solicitudes.forEach((s) => {
      const tr = document.createElement("tr");
      tr.dataset.requestId = s.id;
      const contacto = document.createElement("td");
      contacto.textContent = s.nombre || s.email;
      const small = document.createElement("small");
      small.style.display = "block";
      small.textContent = [s.email, s.telefono].filter(Boolean).join(" \u00b7 ");
      contacto.appendChild(small);
      const detalleTxt = [s.fecha_requerida && `Para ${fecha(s.fecha_requerida)}`, s.cantidad, s.mensaje]
        .filter(Boolean).join(" \u00b7 ");
      const acciones = document.createElement("td");
      acciones.className = "account-actions";
      if (s.estado === "nueva") acciones.appendChild(boton("Marcar respondida", "btn--ghost", { answerId: s.id }));
      tr.append(cell(`#${s.id}`), cell(s.tipo === "cotizacion" ? "Cotizaci\u00f3n" : "Contacto"), contacto,
        cell(s.asunto), cell(detalleTxt), cell(s.estado === "nueva" ? "Nueva" : "Respondida"), acciones);
      tbody.appendChild(tr);
    });
  }

  async function responderSolicitud(id, btn) {
    btn.disabled = true;
    const r = await API().marcarSolicitud(id, "respondida");
    setMsg($("adminRequestsMsg"), r.status === 200 ? `Solicitud #${id} marcada como respondida.` :
      detalle(r, "No se pudo actualizar."), r.status === 200 ? "ok" : "error");
    await cargarSolicitudes();
  }

  // --- admin: productos

  async function cargarProductos() {
    const tbody = $("productsTable").querySelector("tbody");
    const productos = await API().fetchProductos();
    tbody.innerHTML = "";
    productos.forEach((p) => {
      const tr = document.createElement("tr");
      tr.dataset.productId = p.id;
      const mini = document.createElement("td");
      if (p.imagen) {
        const img = document.createElement("img");
        img.className = "admin-thumb";
        img.src = p.imagen;
        img.alt = "";
        img.loading = "lazy";
        img.addEventListener("error", () => img.remove());
        mini.appendChild(img);
      }
      const acciones = document.createElement("td");
      acciones.className = "account-actions";
      acciones.append(
        boton("Editar", "btn--ghost", { editId: p.id }),
        boton("Eliminar", "btn--ghost", { deleteId: p.id })
      );
      tr.append(mini, cell(p.id), cell(p.nombre), cell(p.categoria), cell(String(p.stock ?? "\u2014")),
        cell(API().formatCLP(p.precio)), acciones);
      tbody.appendChild(tr);
    });
    const lista = $("pfCategorias");
    lista.innerHTML = "";
    [...new Set(productos.map((p) => p.categoria))].sort().forEach((c) => {
      const op = document.createElement("option");
      op.value = c;
      lista.appendChild(op);
    });
    return productos;
  }

  async function eliminar(id, btn) {
    const fila = btn.closest("tr");
    const nombre = fila ? fila.children[2].textContent : id;
    if (!window.confirm(`\u00bfEliminar "${nombre}" del cat\u00e1logo? Los pedidos antiguos lo conservan.`)) return;
    btn.disabled = true;
    const r = await API().eliminarProducto(id);
    btn.disabled = false;
    if (r.status === 200) {
      if (fila) fila.remove();
      setMsg($("adminMsg"), `Producto eliminado: ${nombre}.`, "ok");
    } else if (r.status === 401) {
      sesionExpirada();
    } else {
      setMsg($("adminMsg"), detalle(r, "No se pudo eliminar."), "error");
    }
  }

  // --- formulario de producto

  function normalizarTags(texto) {
    const tags = [];
    texto.split(",").forEach((t) => {
      const tag = t.replace(/\s+/g, " ").trim().toLowerCase();
      if (tag && !tags.includes(tag)) tags.push(tag);
    });
    return tags;
  }

  function renderTagsPreview() {
    const cont = $("pfTagsPreview");
    cont.innerHTML = "";
    normalizarTags($("pfTags").value).forEach((t) => {
      const chip = document.createElement("span");
      chip.className = "tag-chip";
      chip.textContent = t;
      cont.appendChild(chip);
    });
  }

  function renderPreviews() {
    const cont = $("pfPreviews");
    cont.innerHTML = "";
    imagenesSeleccionadas.forEach((item, i) => {
      const fig = document.createElement("figure");
      fig.className = "image-preview";
      const img = document.createElement("img");
      img.src = item.url;
      img.alt = item.file.name;
      const pie = document.createElement("figcaption");
      pie.textContent = i === 0 ? "Portada" : item.file.name;
      const quitar = document.createElement("button");
      quitar.type = "button";
      quitar.className = "image-preview__remove";
      quitar.textContent = "\u00d7";
      quitar.setAttribute("aria-label", `Quitar ${item.file.name}`);
      quitar.addEventListener("click", () => {
        URL.revokeObjectURL(item.url);
        imagenesSeleccionadas.splice(i, 1);
        renderPreviews();
      });
      fig.append(img, pie, quitar);
      cont.appendChild(fig);
    });
  }

  function mostrarError(campo, texto) {
    const el = document.querySelector(`[data-error-for="${campo}"]`);
    if (el) {
      el.textContent = texto;
      el.hidden = false;
    }
  }

  function limpiarErrores() {
    document.querySelectorAll("#productForm [data-error-for]").forEach((el) => {
      el.textContent = "";
      el.hidden = true;
    });
    setMsg($("productFormMsg"), "", null);
  }

  function agregarImagenes(files) {
    mostrarError("imagenes", "");
    document.querySelector('[data-error-for="imagenes"]').hidden = true;
    for (const file of files) {
      if (imagenesSeleccionadas.length >= MAX_IMAGENES) {
        mostrarError("imagenes", `M\u00e1ximo ${MAX_IMAGENES} im\u00e1genes.`);
        break;
      }
      if (!TIPOS_IMAGEN.includes(file.type)) {
        mostrarError("imagenes", `${file.name}: solo JPG, PNG o WEBP.`);
        continue;
      }
      if (file.size > MAX_BYTES_IMAGEN) {
        mostrarError("imagenes", `${file.name}: supera los 2 MB.`);
        continue;
      }
      imagenesSeleccionadas.push({ file, url: URL.createObjectURL(file) });
    }
    renderPreviews();
  }

  function validarFormulario() {
    const e = {};
    const n = (id) => Number($(id).value);
    const nombre = $("pfNombre").value.trim();
    const descripcion = $("pfDescripcion").value.trim();
    const categoria = $("pfCategoria").value.trim();
    const tags = normalizarTags($("pfTags").value);
    if (nombre.length < 3 || nombre.length > 80) e.nombre = "Entre 3 y 80 caracteres.";
    if ($("pfPrecio").value === "" || !Number.isInteger(n("pfPrecio")) || n("pfPrecio") < 100 || n("pfPrecio") > 10000000)
      e.precio = "Entero entre $100 y $10.000.000.";
    if (categoria.length < 2 || categoria.length > 30) e.categoria = "Entre 2 y 30 caracteres.";
    if ($("pfStock").value === "" || !Number.isInteger(n("pfStock")) || n("pfStock") < 0 || n("pfStock") > 9999)
      e.stock = "Entero entre 0 y 9999.";
    if (descripcion.length < 10 || descripcion.length > 500) e.descripcion = "Entre 10 y 500 caracteres.";
    if (tags.length > 8 || tags.some((t) => t.length < 2 || t.length > 25)) e.tags = "Hasta 8 tags de 2 a 25 caracteres.";
    if (!editandoId && !imagenesSeleccionadas.length) e.imagenes = "Sube al menos una imagen.";
    return e;
  }

  function abrirFormulario(abrir) {
    $("productForm").hidden = !abrir;
    $("toggleProductForm").setAttribute("aria-expanded", String(abrir));
    $("toggleProductForm").textContent = abrir ? "Cerrar formulario" : "+ Agregar producto";
    if (abrir) $("pfNombre").focus();
  }

  function reiniciarFormulario() {
    $("productForm").reset();
    imagenesSeleccionadas.forEach((it) => URL.revokeObjectURL(it.url));
    imagenesSeleccionadas = [];
    editandoId = null;
    $("productFormTitle").textContent = "Nuevo producto";
    $("pfGuardar").textContent = "Guardar producto";
    $("pfImagenesHint").textContent =
      "De 1 a 5 im\u00e1genes JPG, PNG o WEBP, de hasta 2 MB cada una. La primera es la portada.";
    renderPreviews();
    renderTagsPreview();
    $("pfDescripcionCount").textContent = "0";
    limpiarErrores();
  }

  async function editar(id) {
    const p = await API().fetchProducto(id);
    if (!p) return;
    reiniciarFormulario();
    editandoId = id;
    $("productFormTitle").textContent = `Editar ${p.id}`;
    $("pfGuardar").textContent = "Guardar cambios";
    $("pfImagenesHint").textContent = "Opcional: si subes im\u00e1genes, reemplazan a las actuales.";
    $("pfNombre").value = p.nombre;
    $("pfCategoria").value = p.categoria;
    $("pfPrecio").value = p.precio;
    $("pfStock").value = p.stock;
    $("pfDescripcion").value = p.descripcion;
    $("pfDescripcionCount").textContent = String(p.descripcion.length);
    $("pfTags").value = p.tags.join(", ");
    $("pfIngredientes").value = p.ingredientes || "";
    document.querySelectorAll('#productForm input[name="alergenos"]').forEach((c) => {
      c.checked = (p.alergenos || []).includes(c.value);
    });
    renderTagsPreview();
    abrirFormulario(true);
    $("productForm").scrollIntoView({ behavior: "smooth", block: "start" });
  }

  async function guardarProducto(event) {
    event.preventDefault();
    limpiarErrores();
    const errores = validarFormulario();
    if (Object.keys(errores).length) {
      Object.entries(errores).forEach(([c, t]) => mostrarError(c, t));
      setMsg($("productFormMsg"), "Revisa los campos marcados.", "error");
      return;
    }
    const datos = new FormData();
    datos.append("nombre", $("pfNombre").value.trim());
    datos.append("precio", $("pfPrecio").value);
    datos.append("categoria", $("pfCategoria").value.trim());
    datos.append("stock", $("pfStock").value);
    datos.append("descripcion", $("pfDescripcion").value.trim());
    datos.append("tags", normalizarTags($("pfTags").value).join(","));
    datos.append("ingredientes", $("pfIngredientes").value.trim());
    document.querySelectorAll('#productForm input[name="alergenos"]:checked').forEach((c) => datos.append("alergenos", c.value));
    imagenesSeleccionadas.forEach((it) => datos.append("imagenes", it.file, it.file.name));

    const btn = $("pfGuardar");
    btn.disabled = true;
    const r = editandoId ? await API().editarProducto(editandoId, datos) : await API().crearProducto(datos);
    btn.disabled = false;

    if ((r.status === 201 || r.status === 200) && r.data && r.data.product) {
      const p = r.data.product;
      const verbo = editandoId ? "actualizado" : "agregado";
      reiniciarFormulario();
      abrirFormulario(false);
      setMsg($("adminMsg"), `Producto ${verbo}: ${p.nombre} (${p.id}).`, "ok");
      await cargarProductos();
    } else if (r.status === 400 && r.data && r.data.detail && r.data.detail.errores) {
      Object.entries(r.data.detail.errores).forEach(([c, t]) => mostrarError(c, t));
      setMsg($("productFormMsg"), r.data.detail.mensaje || "Revisa los campos marcados.", "error");
    } else if (r.status === 401) {
      sesionExpirada();
    } else {
      setMsg($("productFormMsg"), detalle(r, "No se pudo guardar el producto. Intenta de nuevo."), "error");
    }
  }

  function initFormulario() {
    $("toggleProductForm").addEventListener("click", () => {
      if ($("productForm").hidden) reiniciarFormulario();
      abrirFormulario($("productForm").hidden);
    });
    $("pfCancelar").addEventListener("click", () => {
      reiniciarFormulario();
      abrirFormulario(false);
    });
    $("productForm").addEventListener("submit", guardarProducto);
    $("pfTags").addEventListener("input", renderTagsPreview);
    $("pfDescripcion").addEventListener("input", () => {
      $("pfDescripcionCount").textContent = String($("pfDescripcion").value.length);
    });
    $("pfImagenes").addEventListener("change", (e) => {
      agregarImagenes(Array.from(e.target.files));
      e.target.value = "";
    });
  }

  // --- vistas y sesion

  async function mostrarCuenta(u) {
    usuarioActual = u;
    $("accountName").textContent = u.username;
    $("accountTipo").textContent = esAdmin(u) ? "Cuenta de administrador" : "Cuenta de cliente";
    actualizarLinkCuenta(u);
    const admin = esAdmin(u);
    $("adminSection").hidden = !admin;
    $("adminOrdersSection").hidden = !admin;
    $("adminRequestsSection").hidden = !admin;
    show("account");
    const params = new URLSearchParams(window.location.search);
    const retorno = params.get("pago") ? params.get("pedido") : null;
    if (retorno) window.history.replaceState({}, "", "cuenta.php");

    const volver = new URLSearchParams(window.location.search).get("volver");
    if (volver === "carrito.php") {
      window.location.href = "carrito.php";
      return;
    }
    await Promise.all([cargarPedidos(), cargarPerfil(), admin ? cargarProductos() : null, admin ? cargarPedidosAdmin() : null,
      admin ? cargarSolicitudes() : null]);
    avisoRetornoPago(retorno);
  }

  async function mostrarLogin(mensaje, tipo = "error") {
    usuarioActual = null;
    actualizarLinkCuenta(null);
    $("loginForm").reset();
    setMsg($("loginMsg"), mensaje || "", mensaje ? tipo : null);
    show("login");
  }

  async function onLogin(e) {
    e.preventDefault();
    const username = $("username").value.trim();
    const password = $("password").value;
    if (!username || !password) return setMsg($("loginMsg"), "Ingresa usuario y contrase\u00f1a.", "error");
    $("loginBtn").disabled = true;
    const r = await API().login(username, password);
    $("loginBtn").disabled = false;
    if (r.status === 200) {
      setMsg($("loginMsg"), "", null);
      await mostrarCuenta(r.data);
    } else if (r.status === 401) {
      setMsg($("loginMsg"), "Usuario o contrase\u00f1a incorrectos.", "error");
      $("password").value = "";
      $("password").focus();
    } else if (r.status === 429) {
      setMsg($("loginMsg"), "Demasiados intentos. Espera un minuto.", "error");
    } else {
      setMsg($("loginMsg"), "No pudimos iniciar sesi\u00f3n en este momento. Intenta de nuevo en unos minutos.", "error");
    }
  }

  async function onRegister(e) {
    e.preventDefault();
    document.querySelectorAll("[data-reg-error]").forEach((el) => (el.hidden = true));
    if (!$("registerForm").reportValidity()) return;
    $("registerBtn").disabled = true;
    const r = await API().registrar($("regUsuario").value.trim().toLowerCase(), $("regClave").value);
    if (r.status !== 201) {
      $("registerBtn").disabled = false;
      const errs = r.data && r.data.detail && r.data.detail.errores;
      if (errs) {
        Object.entries(errs).forEach(([c, t]) => {
          const el = document.querySelector(`[data-reg-error="${c}"]`);
          if (el) {
            el.textContent = t;
            el.hidden = false;
          }
        });
      }
      return setMsg($("registerMsg"), r.status === 429 ? "Demasiados intentos. Espera un minuto." :
        detalle(r, "No se pudo crear la cuenta."), "error");
    }
    const perfil = await API().guardarPerfil({ nombre: $("regNombre").value.trim(), email: $("regCorreo").value.trim() });
    $("registerBtn").disabled = false;
    await mostrarCuenta(r.data);
    if (perfil.status !== 200) {
      setMsg($("profileMsg"), detalle(perfil, "Completa tus datos para poder comprar."), "error");
    }
  }

  async function onLogout() {
    await API().logout();
    await mostrarLogin("Cerraste sesi\u00f3n. \u00a1Te esperamos pronto!", "ok");
  }

  document.addEventListener("DOMContentLoaded", async () => {
    $("loginForm").addEventListener("submit", onLogin);
    $("registerForm").addEventListener("submit", onRegister);
    $("showRegister").addEventListener("click", () => show("register"));
    $("showLogin").addEventListener("click", () => show("login"));
    $("logoutBtn").addEventListener("click", onLogout);
    $("profileForm").addEventListener("submit", guardarPerfil);
    $("adminEstado").addEventListener("change", cargarPedidosAdmin);

    $("ordersTable").addEventListener("click", (e) => {
      const b = e.target.closest("button");
      if (!b) return;
      if (b.dataset.payId) pagar(Number(b.dataset.payId), b);
      if (b.dataset.cancelId) cancelar(Number(b.dataset.cancelId), b);
    });
    $("adminOrdersTable").addEventListener("click", (e) => {
      const b = e.target.closest("button");
      if (!b) return;
      if (b.dataset.setEstado) cambiarEstado(Number(b.dataset.orderId), b.dataset.setEstado, b);
      if (b.dataset.confirmPago) confirmarPago(b.dataset.confirmPago, b);
    });
    $("adminRequestsTable").addEventListener("click", (e) => {
      const b = e.target.closest("button[data-answer-id]");
      if (b) responderSolicitud(Number(b.dataset.answerId), b);
    });
    $("productsTable").addEventListener("click", (e) => {
      const b = e.target.closest("button");
      if (!b) return;
      if (b.dataset.deleteId) eliminar(b.dataset.deleteId, b);
      if (b.dataset.editId) editar(b.dataset.editId);
    });
    initFormulario();

    const u = await API().me();
    if (u) await mostrarCuenta(u);
    else await mostrarLogin();
  });
})();
