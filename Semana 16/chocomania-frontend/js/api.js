// Capa de datos: todo pasa por el API Gateway; el token vive en una cookie HttpOnly.

(function (global) {
  const BASE = ((global.CHOCO_CONFIG || {}).gatewayUrl || "").replace(/\/$/, "");
  const TIMEOUT_MS = 8000;

  // Respaldo inyectado por PHP si el Gateway no responde.
  function respaldoLocal() {
    const r = global.CHOCO_DEMO_PRODUCTS;
    return Array.isArray(r) ? r : [];
  }

  function normalizar(p) {
    return {
      ...p,
      id: String(p.id),
      tags: Array.isArray(p.tags) ? p.tags : [],
      imagenes: Array.isArray(p.imagenes) && p.imagenes.length ? p.imagenes : p.imagen ? [p.imagen] : [],
      categoria: p.categoria || "Otros",
    };
  }

  // Devuelve { status, data }; status 0 = sin respuesta.
  async function request(path, { method = "GET", body, form, timeout = TIMEOUT_MS } = {}) {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), timeout);
    try {
      const opciones = { method, credentials: "include", signal: controller.signal, headers: {} };
      if (form) {
        opciones.body = form; // multipart: el navegador pone el boundary
      } else if (body !== undefined) {
        opciones.headers["Content-Type"] = "application/json";
        opciones.body = JSON.stringify(body);
      }
      const res = await fetch(`${BASE}${path}`, opciones);
      let data = null;
      try {
        data = await res.json();
      } catch (e) {
        data = null;
      }
      return { status: res.status, data };
    } catch (err) {
      return { status: 0, data: null };
    } finally {
      clearTimeout(timer);
    }
  }

  // --- sesion

  let usuarioCache;

  async function login(username, password) {
    const r = await request("/auth/login", { method: "POST", body: { username, password } });
    if (r.status === 200) usuarioCache = r.data;
    return r;
  }

  async function registrar(username, password) {
    const r = await request("/auth/register", { method: "POST", body: { username, password } });
    if (r.status === 201) usuarioCache = r.data;
    return r;
  }

  async function me() {
    if (usuarioCache !== undefined) return usuarioCache;
    const r = await request("/auth/me");
    usuarioCache = r.status === 200 && r.data && r.data.username ? r.data : null;
    return usuarioCache;
  }

  async function logout() {
    const r = await request("/auth/logout", { method: "POST" });
    usuarioCache = null;
    return r;
  }

  // --- catalogo (inventory)

  let cache = null;
  let origenDatos = null;

  async function fetchProductos() {
    if (cache) return cache;
    const r = await request("/api/products?tamano=50");
    const enVivo = r.status === 200 && r.data && Array.isArray(r.data.products);
    origenDatos = enVivo ? "gateway" : "respaldo";
    cache = (enVivo ? r.data.products : respaldoLocal()).map(normalizar);
    return cache;
  }

  async function fetchProducto(id) {
    if (!id) return null;
    const r = await request(`/api/products/${encodeURIComponent(id)}`);
    if (r.status === 200 && r.data && r.data.product) return normalizar(r.data.product);
    if (r.status === 404) return null;
    const todos = await fetchProductos();
    return todos.find((p) => p.id === String(id)) || null;
  }

  function invalidar(r, ...ok) {
    if (ok.includes(r.status)) cache = null;
    return r;
  }

  const crearProducto = async (form) =>
    invalidar(await request("/api/products", { method: "POST", form, timeout: 30000 }), 201);
  const editarProducto = async (id, form) =>
    invalidar(await request(`/api/products/${encodeURIComponent(id)}`, { method: "PUT", form, timeout: 30000 }), 200);
  const eliminarProducto = async (id) =>
    invalidar(await request(`/api/products/${encodeURIComponent(id)}`, { method: "DELETE" }), 200);

  // --- clientes, pedidos y pagos

  const miPerfil = () => request("/api/clients/me");
  const guardarPerfil = (perfil) => request("/api/clients/me", { method: "PUT", body: perfil });

  const crearPedido = async (pedido) => invalidar(await request("/api/orders", { method: "POST", body: pedido }), 201);
  const fetchPedidos = () => request("/api/orders");
  const cancelarPedido = async (id) =>
    invalidar(await request(`/api/orders/${encodeURIComponent(id)}/cancel`, { method: "POST" }), 200);
  const cambiarEstado = (id, estado, motivo = "") =>
    request(`/api/admin/orders/${encodeURIComponent(id)}/estado`, { method: "PATCH", body: { estado, motivo } });

  const iniciarPago = (pedidoId) => request("/api/payments", { method: "POST", body: { pedido_id: Number(pedidoId) } });
  const confirmarTransferencia = (pagoId) =>
    request(`/api/admin/payments/${encodeURIComponent(pagoId)}/confirmar`, { method: "POST" });

  // Cotizaciones y contacto (clients).
  const enviarSolicitud = (datos) => request("/api/solicitudes", { method: "POST", body: datos });
  const adminSolicitudes = (estado) => request(`/api/admin/solicitudes${estado ? `?estado=${estado}` : ""}`);
  const marcarSolicitud = (id, estado) =>
    request(`/api/admin/solicitudes/${encodeURIComponent(id)}`, { method: "PATCH", body: { estado } });

  // Consulta GraphQL agregada.
  async function graphql(query, variables = {}) {
    const r = await request("/api/graphql", { method: "POST", body: { query, variables } });
    return { status: r.status, data: r.data && r.data.data, errors: (r.data && r.data.errors) || [] };
  }

  function formatCLP(numero) {
    return "$" + Math.round(Number(numero) || 0).toLocaleString("es-CL");
  }

  global.ChocoAPI = {
    login,
    registrar,
    me,
    logout,
    fetchProductos,
    fetchProducto,
    crearProducto,
    editarProducto,
    eliminarProducto,
    miPerfil,
    guardarPerfil,
    crearPedido,
    fetchPedidos,
    cancelarPedido,
    cambiarEstado,
    iniciarPago,
    confirmarTransferencia,
    graphql,
    enviarSolicitud,
    adminSolicitudes,
    marcarSolicitud,
    formatCLP,
    get origenDatos() {
      return origenDatos;
    },
  };
})(window);
