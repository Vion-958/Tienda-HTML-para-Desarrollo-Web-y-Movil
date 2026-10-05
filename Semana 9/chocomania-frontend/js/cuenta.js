/* ChocoManía — página Mi cuenta.
   Login, usuario actual, pedidos, operación de administrador y logout.
   Todo pasa por window.ChocoAPI (js/api.js), que habla con el Gateway.
   El token nunca aparece aquí: vive en una cookie HttpOnly. */

(function () {
  const $ = (id) => document.getElementById(id);

  const ESTADOS = { paid: "Pagado", pending: "Pendiente" };

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

  function actualizarLinkCuenta(usuario) {
    document.querySelectorAll("[data-account-link]").forEach((a) => {
      a.textContent = usuario ? `Hola, ${usuario.username}` : "Mi cuenta";
    });
  }

  // -------------------------------------------------------------------
  // Pedidos
  // -------------------------------------------------------------------

  async function cargarPedidos() {
    const msg = $("ordersMsg");
    const tabla = $("ordersTable");
    const tbody = tabla.querySelector("tbody");
    tbody.innerHTML = "";

    const r = await window.ChocoAPI.fetchPedidos();
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
      const unidades = p.items.reduce((acc, it) => acc + it.cantidad, 0);
      tr.append(
        cell(`#${p.id}`),
        cell(p.cliente),
        cell(ESTADOS[p.status] || p.status),
        cell(`${unidades} unidad${unidades === 1 ? "" : "es"}`),
        cell(window.ChocoAPI.formatCLP(p.total))
      );
      tbody.appendChild(tr);
    });
    msg.hidden = true;
    tabla.hidden = false;
  }

  // -------------------------------------------------------------------
  // Administración de productos
  // -------------------------------------------------------------------

  async function cargarProductos() {
    const tbody = $("productsTable").querySelector("tbody");
    tbody.innerHTML = "";
    const productos = await window.ChocoAPI.fetchProductos();

    productos.forEach((p) => {
      const tr = document.createElement("tr");
      tr.dataset.productId = p.id;

      const acciones = document.createElement("td");
      acciones.style.textAlign = "right";
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "btn btn--sm btn--ghost";
      btn.textContent = "Eliminar";
      btn.setAttribute("aria-label", `Eliminar ${p.nombre}`);
      btn.dataset.deleteId = p.id;
      acciones.appendChild(btn);

      tr.append(cell(p.id), cell(p.nombre), cell(window.ChocoAPI.formatCLP(p.precio)), acciones);
      tbody.appendChild(tr);
    });
  }

  async function eliminar(id, boton) {
    const fila = boton.closest("tr");
    const nombre = fila ? fila.children[1].textContent : id;
    if (!window.confirm(`¿Eliminar "${nombre}" del catálogo?`)) return;

    const msg = $("adminMsg");
    boton.disabled = true;
    const r = await window.ChocoAPI.eliminarProducto(id);
    boton.disabled = false;

    if (r.status === 200) {
      if (fila) fila.remove();
      setMsg(msg, `Producto eliminado: ${nombre} (200 OK).`, "ok");
    } else if (r.status === 403) {
      setMsg(msg, "No autorizado (403): tu usuario no tiene el rol admin.", "error");
    } else if (r.status === 401) {
      setMsg(msg, "", null);
      await mostrarLogin("Tu sesión expiró (401). Vuelve a iniciar sesión.");
    } else if (r.status === 404) {
      if (fila) fila.remove();
      setMsg(msg, "Ese producto ya no existe (404).", "error");
    } else {
      setMsg(msg, `No se pudo eliminar (código ${r.status || "sin respuesta"}).`, "error");
    }
  }

  // -------------------------------------------------------------------
  // Vistas
  // -------------------------------------------------------------------

  async function mostrarCuenta(usuario) {
    $("accountName").textContent = usuario.username;
    $("accountId").textContent = usuario.user_id;
    $("accountRoles").textContent = usuario.roles.join(", ");
    actualizarLinkCuenta(usuario);
    setMsg($("adminMsg"), "", null);
    show("account");
    await Promise.all([cargarPedidos(), cargarProductos()]);
  }

  async function mostrarLogin(mensaje, tipo = "error") {
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

    const usuario = await window.ChocoAPI.me();
    if (usuario) {
      await mostrarCuenta(usuario);
    } else {
      await mostrarLogin();
    }
  });
})();
