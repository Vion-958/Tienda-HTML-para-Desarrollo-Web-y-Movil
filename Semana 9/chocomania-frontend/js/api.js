/* ChocoManía — capa de datos y sesión (Semana 9).
   El sitio se abre a través del API Gateway (http://localhost:8000), que
   también lo sirve. Por eso todas las llamadas son del mismo origen:

     Navegador --cookie session_token (HttpOnly)--> Gateway :8000
                         |  introspección (Auth Service) + roles + Vault
                         v
                  Backend API :9000

   El token de sesión NUNCA pasa por JavaScript: el Gateway lo guarda en
   una cookie HttpOnly al hacer login y el navegador la envía solo. Aquí no
   hay localStorage ni "Authorization: Bearer ..." armado a mano.

   Sin sesión (o si el Gateway no está), el catálogo usa el respaldo local
   para que el sitio siga siendo 100% navegable. */

(function (global) {
  const CONFIG = Object.assign(
    {
      // Vacío = mismo origen (el sitio servido por el Gateway).
      gatewayUrl: "",
    },
    global.CHOCO_CONFIG || {}
  );

  const BASE = CONFIG.gatewayUrl.replace(/\/$/, "");
  const REQUEST_TIMEOUT_MS = 4000;

  const DEMO_PRODUCTS = [
    {
      id: "demo-1",
      nombre: "Torta tres leches de chocolate",
      precio: 15800,
      descripcion: "Bizcocho húmedo bañado en tres leches con cobertura de chocolate.",
      imagen: "https://images.unsplash.com/photo-1464349095431-e9a21285b5f3?q=80&w=500&auto=format&fit=crop",
      categoria: "De leche",
    },
    {
      id: "demo-2",
      nombre: "Torta frutos del bosque",
      precio: 16600,
      descripcion: "Bizcocho de vainilla, crema chantilly y frutos rojos frescos.",
      imagen: "https://images.unsplash.com/photo-1578985545062-69928b1d9587?q=80&w=500&auto=format&fit=crop",
      categoria: "De leche",
    },
    {
      id: "demo-3",
      nombre: "Torta de cumpleaños",
      precio: 17900,
      descripcion: "Personalizable con mensaje y color a elección.",
      imagen: "https://images.unsplash.com/photo-1621303837174-89787a7d4729?q=80&w=500&auto=format&fit=crop",
      categoria: "De leche",
    },
    {
      id: "demo-4",
      nombre: "Caja de cupcakes surtidos",
      precio: 6500,
      descripcion: "Chocolate, red velvet y limón. Caja de 3 unidades.",
      imagen: "https://images.unsplash.com/photo-1517427294546-5aa121f68e8a?q=80&w=500&auto=format&fit=crop",
      categoria: "Postres",
    },
    {
      id: "demo-5",
      nombre: "Brownie de chocolate 70%",
      precio: 4200,
      descripcion: "Chocolate 70% cacao con nueces tostadas.",
      imagen: "https://images.unsplash.com/photo-1550617931-e17a7b70dce2?q=80&w=500&auto=format&fit=crop",
      categoria: "Amargo",
    },
    {
      id: "demo-6",
      nombre: "Torta red velvet",
      precio: 18500,
      descripcion: "Bizcocho aterciopelado con relleno de queso crema y toque de cacao.",
      imagen: "https://images.unsplash.com/photo-1621303837174-89787a7d4729?q=80&w=500&auto=format&fit=crop",
      categoria: "De leche",
    },
    {
      id: "demo-7",
      nombre: "Alfajores bañados en chocolate",
      precio: 5200,
      descripcion: "Alfajores artesanales rellenos de manjar, bañados en chocolate con leche.",
      imagen: "https://images.unsplash.com/photo-1517427294546-5aa121f68e8a?q=80&w=500&auto=format&fit=crop",
      categoria: "De leche",
    },
    {
      id: "demo-8",
      nombre: "Barra chocolate amargo 85%",
      precio: 4800,
      descripcion: "Chocolate 85% cacao de origen único, intenso y sin relleno.",
      imagen: "https://images.unsplash.com/photo-1550617931-e17a7b70dce2?q=80&w=500&auto=format&fit=crop",
      categoria: "Amargo",
    },
    {
      id: "demo-9",
      nombre: "Trufas de chocolate amargo",
      precio: 6900,
      descripcion: "Trufas artesanales con ganache 70% cacao y cobertura amarga.",
      imagen: "img/servicio-cocteles.jpg",
      categoria: "Amargo",
    },
    {
      id: "demo-10",
      nombre: "Torta vegana de chocolate",
      precio: 19900,
      descripcion: "Bizcocho 100% plant-based con ganache vegano, sin huevo ni lácteos.",
      imagen: "https://images.unsplash.com/photo-1464349095431-e9a21285b5f3?q=80&w=500&auto=format&fit=crop",
      categoria: "Vegana",
    },
    {
      id: "demo-11",
      nombre: "Brownie vegano sin gluten",
      precio: 4700,
      descripcion: "Brownie húmedo con harina de almendras, sin gluten, huevo ni lácteos.",
      imagen: "https://images.unsplash.com/photo-1550617931-e17a7b70dce2?q=80&w=500&auto=format&fit=crop",
      categoria: "Vegana",
    },
    {
      id: "demo-12",
      nombre: "Chocolate sin azúcar con stevia",
      precio: 5500,
      descripcion: "Barra de chocolate endulzada con stevia, ideal para un consumo más consciente.",
      imagen: "https://images.unsplash.com/photo-1550617931-e17a7b70dce2?q=80&w=500&auto=format&fit=crop",
      categoria: "Sin azúcar",
    },
    {
      id: "demo-13",
      nombre: "Bombones sin azúcar surtidos",
      precio: 7200,
      descripcion: "Caja de bombones rellenos endulzados con maltitol, sin azúcar añadida.",
      imagen: "img/servicio-cocteles.jpg",
      categoria: "Sin azúcar",
    },
    {
      id: "demo-14",
      nombre: "Caja por mayor 50 chocolates",
      precio: 45000,
      descripcion: "Caja al por mayor con 50 chocolates surtidos, ideal para eventos y revendedores.",
      imagen: "img/servicio-regalos.png",
      categoria: "Por mayor",
    },
    {
      id: "demo-15",
      nombre: "Pack por mayor 100 mini brownies",
      precio: 62000,
      descripcion: "Pack al por mayor de 100 mini brownies individuales, precio especial por volumen.",
      imagen: "img/servicio-regalos.png",
      categoria: "Por mayor",
    },
  ];

  // Reglas de respaldo para clasificar productos que no traigan
  // "categoria" propia.
  const CATEGORY_RULES = [
    { categoria: "Vegana", test: /vegan/i },
    { categoria: "Sin azúcar", test: /sin azúcar|stevia|maltitol/i },
    { categoria: "Por mayor", test: /por mayor|al por mayor/i },
    { categoria: "De leche", test: /torta|leches|cumplea|alfajor/i },
    { categoria: "Postres", test: /brownie|cupcake|pie|croissant|pastel/i },
    { categoria: "Amargo", test: /70%|85%|amargo|cacao/i },
  ];

  function tagCategoria(producto) {
    const normalizado = { ...producto, id: String(producto.id) };
    if (normalizado.categoria) return normalizado;
    const texto = `${normalizado.nombre} ${normalizado.descripcion || ""}`;
    const regla = CATEGORY_RULES.find((r) => r.test.test(texto));
    return { ...normalizado, categoria: regla ? regla.categoria : "Otros" };
  }

  /* Llamada al Gateway. Devuelve siempre { status, data }:
       status 0  -> no hubo respuesta (Gateway caído, timeout, sin red)
       data null -> la respuesta no traía JSON */
  async function request(path, options = {}) {
    if (!global.fetch) return { status: 0, data: null };
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);
    try {
      const headers = {};
      if (options.body !== undefined) headers["Content-Type"] = "application/json";
      const res = await fetch(`${BASE}${path}`, {
        method: options.method || "GET",
        headers,
        credentials: "include",
        body: options.body !== undefined ? JSON.stringify(options.body) : undefined,
        signal: controller.signal,
      });
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

  // ---------------------------------------------------------------------
  // Sesión
  // ---------------------------------------------------------------------

  let usuarioCache;

  async function login(username, password) {
    const r = await request("/auth/login", { method: "POST", body: { username, password } });
    if (r.status === 200) {
      usuarioCache = r.data;
      cache = null;
    }
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
    cache = null;
    return r;
  }

  // ---------------------------------------------------------------------
  // Catálogo y pedidos
  // ---------------------------------------------------------------------

  let cache = null;
  let origenDatos = null; // "gateway" o "respaldo"

  function respaldoLocal() {
    // Cada página .php declara su propio arreglo de productos en PHP y lo
    // vuelca a JS con json_encode. Si la página lo define, se usa ese
    // respaldo; si no, se cae al arreglo fijo de este archivo.
    const inyectado = global.CHOCO_DEMO_PRODUCTS;
    return Array.isArray(inyectado) && inyectado.length ? inyectado : DEMO_PRODUCTS;
  }

  async function fetchProductos() {
    if (cache) return cache;
    const r = await request("/api/products");
    const enVivo = r.status === 200 && r.data && Array.isArray(r.data.products);
    origenDatos = enVivo ? "gateway" : "respaldo";
    if (!enVivo) {
      console.info(
        r.status === 401
          ? "[ChocoAPI] Sin sesión: se muestra el catálogo de respaldo. Inicia sesión en Mi cuenta."
          : "[ChocoAPI] Gateway no disponible: se muestra el catálogo de respaldo."
      );
    }
    cache = (enVivo ? r.data.products : respaldoLocal()).map(tagCategoria);
    return cache;
  }

  async function fetchProducto(id) {
    if (!id) return null;
    const r = await request(`/api/products/${encodeURIComponent(id)}`);
    if (r.status === 200 && r.data && r.data.product) {
      origenDatos = "gateway";
      return tagCategoria(r.data.product);
    }
    const todos = await fetchProductos();
    return todos.find((p) => p.id === String(id)) || null;
  }

  async function fetchPedidos() {
    return request("/api/orders");
  }

  async function eliminarProducto(id) {
    const r = await request(`/api/products/${encodeURIComponent(id)}`, { method: "DELETE" });
    if (r.status === 200) cache = null;
    return r;
  }

  function formatCLP(numero) {
    const valor = Math.round(Number(numero) || 0);
    return "$" + valor.toLocaleString("es-CL");
  }

  global.ChocoAPI = {
    login,
    me,
    logout,
    fetchProductos,
    fetchProducto,
    fetchPedidos,
    eliminarProducto,
    formatCLP,
    get origenDatos() {
      return origenDatos;
    },
  };
})(window);
