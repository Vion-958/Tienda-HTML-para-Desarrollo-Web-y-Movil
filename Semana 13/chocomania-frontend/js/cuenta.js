/* ChocoManía — página Mi cuenta.
   Login, usuario actual, pedidos (con cancelación), administración
   (solo rol admin: agregar y eliminar productos) y logout.
   Todo pasa por window.ChocoAPI (js/api.js), que habla con el Gateway.
   El token nunca aparece aquí: vive en una cookie HttpOnly. */

(function () {
  const $ = (id) => document.getElementById(id);

  const ESTADOS = { paid: "Pagado", pending: "Pendiente", cancelled: "Cancelado" };

  // Mismas reglas que valida el Backend (backend_api.py). Validar también
  // aquí solo mejora la experiencia: quien decide es el servidor.
  const MAX_IMAGENES = 5;
  const MAX_BYTES_IMAGEN = 2 * 1024 * 1024;
  const TIPOS_IMAGEN = ["image/jpeg", "image/png", "image/webp"];

  let usuarioActual = null;
  let imagenesSeleccionadas = []; // [{ file, url }]

  function show(section) {
    $("accountLoading").hidden = true;
    $("loginSection").hidden = section !== "login";
    $("accountSection").hidden = section !== "account";
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

  function esAdmin(usuario) {
    return Boolean(usuario && usuario.roles.includes("admin"));
  }

  function actualizarLinkCuenta(usuario) {
    document.querySelectorAll("[data-account-link]").forEach((a) => {
      a.textContent = usuario ? `Hola, ${usuario.username}` : "Mi cuenta";
    });
  }

  function detalleError(r, porDefecto) {
    const d = r.data && r.data.detail;
    if (typeof d === "string") return d;
    if (d && typeof d.mensaje === "string") return d.mensaje;
    return porDefecto;
  }

  // -------------------------------------------------------------------
  // Pedidos
  // -------------------------------------------------------------------

  async function cargarPedidos() {
    const msg = $("ordersMsg");
    const tabla = $("ordersTable");
    const tbody = tabla.querySelector("tbody");

    // Las filas se reemplazan recién cuando llega la respuesta, para que la
    // tabla no quede vacía mientras se recarga.
    const r = await window.ChocoAPI.fetchPedidos();
    tbody.innerHTML = "";
    if (r.status !== 200 || !r.data) {
      tabla.hidden = true;
      msg.hidden = false;
      msg.textContent = `No se pudieron cargar los pedidos (código ${r.status || "sin respuesta"}).`;
      return;
    }

    const pedidos = r.data.orders || [];
    if (!pedidos.length) {
      tabla.hidden = true;
      msg.hidden = false;
      msg.textContent = "Aún no tienes pedidos.";
      return;
    }

    pedidos.forEach((p) => {
      const tr = document.createElement("tr");
      tr.dataset.orderId = p.id;
      const unidades = p.items.reduce((acc, it) => acc + it.cantidad, 0);

      const estado = document.createElement("td");
      const etiqueta = document.createElement("span");
      etiqueta.className = `order-status order-status--${p.status}`;
      etiqueta.textContent = ESTADOS[p.status] || p.status;
      estado.appendChild(etiqueta);

      // Solo quien hizo el pedido puede cancelarlo, y solo si está pendiente.
      const acciones = document.createElement("td");
      acciones.style.textAlign = "right";
      if (usuarioActual && p.user_id === usuarioActual.user_id && p.status === "pending") {
        const btn = document.createElement("button");
        btn.type = "button";
        btn.className = "btn btn--sm btn--ghost";
        btn.textContent = "Cancelar";
        btn.setAttribute("aria-label", `Cancelar pedido ${p.id}`);
        btn.dataset.cancelId = p.id;
        acciones.appendChild(btn);
      }

      tr.append(
        cell(`#${p.id}`),
        cell(p.cliente),
        estado,
        cell(`${unidades} unidad${unidades === 1 ? "" : "es"}`),
        cell(window.ChocoAPI.formatCLP(p.total)),
        acciones
      );
      if (p.status === "cancelled") tr.classList.add("is-cancelled");
      tbody.appendChild(tr);
    });
    msg.hidden = true;
    tabla.hidden = false;
  }

  async function cancelarPedido(id, boton) {
    if (!window.confirm(`¿Cancelar el pedido #${id}? Esta acción no se puede deshacer.`)) return;

    const msg = $("orderActionMsg");
    boton.disabled = true;
    const r = await window.ChocoAPI.cancelarPedido(id);
    boton.disabled = false;

    if (r.status === 200) {
      setMsg(msg, `Pedido #${id} cancelado.`, "ok");
      await cargarPedidos();
      if (esAdmin(usuarioActual)) await cargarProductos(); // el stock volvió
    } else if (r.status === 401) {
      setMsg(msg, "", null);
      await mostrarLogin("Tu sesión expiró. Vuelve a iniciar sesión.");
    } else if (r.status === 404 || r.status === 409) {
      setMsg(msg, detalleError(r, "No se pudo cancelar el pedido."), "error");
      await cargarPedidos();
    } else {
      setMsg(msg, `No se pudo cancelar el pedido (código ${r.status || "sin respuesta"}).`, "error");
    }
  }

  // -------------------------------------------------------------------
  // Administración: listado y eliminación
  // -------------------------------------------------------------------

  async function cargarProductos() {
    const tbody = $("productsTable").querySelector("tbody");
    const productos = await window.ChocoAPI.fetchProductos();
    tbody.innerHTML = "";

    productos.forEach((p) => {
      const tr = document.createElement("tr");
      tr.dataset.productId = p.id;

      const miniatura = document.createElement("td");
      if (p.imagen) {
        const img = document.createElement("img");
        img.className = "admin-thumb";
        img.src = p.imagen;
        img.alt = "";
        img.loading = "lazy";
        img.addEventListener("error", () => img.remove());
        miniatura.appendChild(img);
      }

      const acciones = document.createElement("td");
      acciones.style.textAlign = "right";
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "btn btn--sm btn--ghost";
      btn.textContent = "Eliminar";
      btn.setAttribute("aria-label", `Eliminar ${p.nombre}`);
      btn.dataset.deleteId = p.id;
      acciones.appendChild(btn);

      const stock = p.stock === undefined ? "—" : String(p.stock);
      tr.append(
        miniatura,
        cell(p.id),
        cell(p.nombre),
        cell(p.categoria),
        cell(stock),
        cell(window.ChocoAPI.formatCLP(p.precio)),
        acciones
      );
      tbody.appendChild(tr);
    });

    // Sugerencias de categoría para el formulario.
    const lista = $("pfCategorias");
    lista.innerHTML = "";
    [...new Set(productos.map((p) => p.categoria))].sort().forEach((c) => {
      const op = document.createElement("option");
      op.value = c;
      lista.appendChild(op);
    });
  }

  async function eliminar(id, boton) {
    const fila = boton.closest("tr");
    const nombre = fila ? fila.children[2].textContent : id;
    if (!window.confirm(`¿Eliminar "${nombre}" del catálogo?`)) return;

    const msg = $("adminMsg");
    boton.disabled = true;
    const r = await window.ChocoAPI.eliminarProducto(id);
    boton.disabled = false;

    if (r.status === 200) {
      if (fila) fila.remove();
      setMsg(msg, `Producto eliminado: ${nombre}.`, "ok");
    } else if (r.status === 403) {
      setMsg(msg, "No autorizado: tu usuario no tiene el rol admin.", "error");
    } else if (r.status === 401) {
      setMsg(msg, "", null);
      await mostrarLogin("Tu sesión expiró. Vuelve a iniciar sesión.");
    } else if (r.status === 404) {
      if (fila) fila.remove();
      setMsg(msg, "Ese producto ya no existe.", "error");
    } else {
      setMsg(msg, `No se pudo eliminar (código ${r.status || "sin respuesta"}).`, "error");
    }
  }

  // -------------------------------------------------------------------
  // Administración: nuevo producto
  // -------------------------------------------------------------------

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
    normalizarTags($("pfTags").value).forEach((tag) => {
      const chip = document.createElement("span");
      chip.className = "tag-chip";
      chip.textContent = tag;
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
      quitar.textContent = "×";
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

  function agregarImagenes(files) {
    limpiarError("imagenes");
    for (const file of files) {
      if (imagenesSeleccionadas.length >= MAX_IMAGENES) {
        mostrarError("imagenes", `Máximo ${MAX_IMAGENES} imágenes.`);
        break;
      }
      if (!TIPOS_IMAGEN.includes(file.type)) {
        mostrarError("imagenes", `${file.name}: solo se aceptan JPG, PNG o WEBP.`);
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

  function mostrarError(campo, texto) {
    const el = document.querySelector(`[data-error-for="${campo}"]`);
    if (el) {
      el.textContent = texto;
      el.hidden = false;
    }
  }

  function limpiarError(campo) {
    const el = document.querySelector(`[data-error-for="${campo}"]`);
    if (el) {
      el.textContent = "";
      el.hidden = true;
    }
  }

  function limpiarErrores() {
    document.querySelectorAll("#productForm [data-error-for]").forEach((el) => {
      el.textContent = "";
      el.hidden = true;
    });
    setMsg($("productFormMsg"), "", null);
  }

  function validarFormulario() {
    const errores = {};
    const nombre = $("pfNombre").value.trim();
    const precio = Number($("pfPrecio").value);
    const stock = Number($("pfStock").value);
    const categoria = $("pfCategoria").value.trim();
    const descripcion = $("pfDescripcion").value.trim();
    const tags = normalizarTags($("pfTags").value);

    if (nombre.length < 3 || nombre.length > 80) errores.nombre = "Entre 3 y 80 caracteres.";
    if ($("pfPrecio").value === "" || !Number.isInteger(precio) || precio < 100 || precio > 10000000)
      errores.precio = "Número entero entre $100 y $10.000.000.";
    if (categoria.length < 2 || categoria.length > 30) errores.categoria = "Entre 2 y 30 caracteres.";
    if ($("pfStock").value === "" || !Number.isInteger(stock) || stock < 0 || stock > 9999)
      errores.stock = "Número entero entre 0 y 9999.";
    if (descripcion.length < 10 || descripcion.length > 500) errores.descripcion = "Entre 10 y 500 caracteres.";
    if (tags.length > 8 || tags.some((t) => t.length < 2 || t.length > 25))
      errores.tags = "Hasta 8 tags de 2 a 25 caracteres.";
    if (!imagenesSeleccionadas.length) errores.imagenes = "Sube al menos una imagen.";
    return errores;
  }

  function abrirFormulario(abrir) {
    const form = $("productForm");
    form.hidden = !abrir;
    $("toggleProductForm").setAttribute("aria-expanded", String(abrir));
    $("toggleProductForm").textContent = abrir ? "Cerrar formulario" : "+ Agregar producto";
    if (abrir) $("pfNombre").focus();
  }

  function reiniciarFormulario() {
    $("productForm").reset();
    imagenesSeleccionadas.forEach((it) => URL.revokeObjectURL(it.url));
    imagenesSeleccionadas = [];
    renderPreviews();
    renderTagsPreview();
    $("pfDescripcionCount").textContent = "0";
    limpiarErrores();
  }

  async function guardarProducto(event) {
    event.preventDefault();
    limpiarErrores();

    const errores = validarFormulario();
    if (Object.keys(errores).length) {
      Object.entries(errores).forEach(([campo, texto]) => mostrarError(campo, texto));
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
    document.querySelectorAll('#productForm input[name="alergenos"]:checked').forEach((c) => {
      datos.append("alergenos", c.value);
    });
    imagenesSeleccionadas.forEach((it) => datos.append("imagenes", it.file, it.file.name));

    const boton = $("pfGuardar");
    boton.disabled = true;
    boton.textContent = "Guardando…";
    const r = await window.ChocoAPI.crearProducto(datos);
    boton.disabled = false;
    boton.textContent = "Guardar producto";

    if (r.status === 201 && r.data && r.data.product) {
      const p = r.data.product;
      reiniciarFormulario();
      abrirFormulario(false);
      setMsg($("adminMsg"), `Producto agregado: ${p.nombre} (${p.id}). Ya aparece en el catálogo.`, "ok");
      await cargarProductos();
    } else if (r.status === 400 && r.data && r.data.detail && r.data.detail.errores) {
      Object.entries(r.data.detail.errores).forEach(([campo, texto]) => mostrarError(campo, texto));
      setMsg($("productFormMsg"), r.data.detail.mensaje || "Revisa los campos marcados.", "error");
    } else if (r.status === 403) {
      setMsg($("productFormMsg"), "No autorizado: tu usuario no tiene el rol admin.", "error");
    } else if (r.status === 401) {
      await mostrarLogin("Tu sesión expiró. Vuelve a iniciar sesión.");
    } else if (r.status === 413) {
      setMsg($("productFormMsg"), "Las imágenes pesan demasiado. Prueba con archivos más livianos.", "error");
    } else {
      setMsg($("productFormMsg"), `No se pudo guardar el producto (código ${r.status || "sin respuesta"}).`, "error");
    }
  }

  function initFormulario() {
    $("toggleProductForm").addEventListener("click", () => abrirFormulario($("productForm").hidden));
    $("pfCancelar").addEventListener("click", () => {
      reiniciarFormulario();
      abrirFormulario(false);
    });
    $("productForm").addEventListener("submit", guardarProducto);
    $("pfTags").addEventListener("input", renderTagsPreview);
    $("pfDescripcion").addEventListener("input", () => {
      $("pfDescripcionCount").textContent = String($("pfDescripcion").value.length);
    });
    $("pfImagenes").addEventListener("change", (event) => {
      agregarImagenes(Array.from(event.target.files));
      event.target.value = ""; // permite volver a elegir el mismo archivo
    });
  }

  // -------------------------------------------------------------------
  // Vistas
  // -------------------------------------------------------------------

  async function mostrarCuenta(usuario) {
    usuarioActual = usuario;
    $("accountName").textContent = usuario.username;
    $("accountId").textContent = usuario.user_id;
    $("accountRoles").textContent = usuario.roles.join(", ");
    actualizarLinkCuenta(usuario);
    setMsg($("adminMsg"), "", null);
    setMsg($("orderActionMsg"), "", null);

    // La administración solo se muestra al rol admin. Es solo presentación:
    // quien autoriza de verdad es el Gateway y el Backend (403 para los demás).
    const admin = esAdmin(usuario);
    $("adminSection").hidden = !admin;
    if (!admin) {
      $("productsTable").querySelector("tbody").innerHTML = "";
      reiniciarFormulario();
      abrirFormulario(false);
    }

    show("account");
    await Promise.all([cargarPedidos(), admin ? cargarProductos() : Promise.resolve()]);
  }

  async function mostrarLogin(mensaje, tipo = "error") {
    usuarioActual = null;
    actualizarLinkCuenta(null);
    $("loginForm").reset();
    setMsg($("loginMsg"), mensaje || "", mensaje ? tipo : null);
    show("login");
  }

  async function onLogin(event) {
    event.preventDefault();
    const username = $("username").value.trim();
    const password = $("password").value;
    const msg = $("loginMsg");

    if (!username || !password) {
      setMsg(msg, "Ingresa usuario y contraseña.", "error");
      return;
    }

    $("loginBtn").disabled = true;
    const r = await window.ChocoAPI.login(username, password);
    $("loginBtn").disabled = false;

    if (r.status === 200) {
      setMsg(msg, "", null);
      await mostrarCuenta(r.data);
    } else if (r.status === 401) {
      setMsg(msg, "Usuario o contraseña incorrectos (401).", "error");
      $("password").value = "";
      $("password").focus();
    } else if (r.status === 0 || r.status === 404) {
      setMsg(msg, "No se encontró el API Gateway. Abre el sitio desde http://localhost:8000.", "error");
    } else {
      setMsg(msg, `El servicio de autenticación no está disponible (${r.status}).`, "error");
    }
  }

  async function onLogout() {
    await window.ChocoAPI.logout();
    await mostrarLogin("Cerraste sesión. La sesión fue revocada en el servidor.", "ok");
  }

  document.addEventListener("DOMContentLoaded", async () => {
    $("loginForm").addEventListener("submit", onLogin);
    $("logoutBtn").addEventListener("click", onLogout);
    $("productsTable").addEventListener("click", (event) => {
      const btn = event.target.closest("[data-delete-id]");
      if (btn) eliminar(btn.dataset.deleteId, btn);
    });
    $("ordersTable").addEventListener("click", (event) => {
      const btn = event.target.closest("[data-cancel-id]");
      if (btn) cancelarPedido(Number(btn.dataset.cancelId), btn);
    });
    initFormulario();

    const usuario = await window.ChocoAPI.me();
    if (usuario) {
      await mostrarCuenta(usuario);
    } else {
      await mostrarLogin();
    }
  });
})();
