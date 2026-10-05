/* ChocoManía — capa de datos (Semana 8).
   El sitio ya no habla directo con el backend: todas las solicitudes
   pasan por el API Gateway (FastAPI + Vault), que exige un Bearer token.

     Navegador --Authorization: Bearer <token>--> Gateway :8000
                                                    |  valida el token contra Vault
                                                    v
                                       Backend API :9000 (/products)

   Si el Gateway no responde, rechaza el token o el navegador bloquea la
   petición, se usa un catálogo de respaldo con los mismos productos,
   para que el sitio siga siendo 100% navegable de forma independiente.

   Configuración: los valores por defecto se pueden sobrescribir antes de
   cargar este archivo, por ejemplo:
     <script>window.CHOCO_CONFIG = { gatewayUrl: "http://192.168.1.10:8000",
                                     clientToken: "nuevo-token-789" };</script>

   Nota de seguridad: en un sitio web el token del cliente queda visible
   en el navegador. Aquí representa la identidad del "cliente web"; nunca
   se usa el secreto interno Gateway-Backend, que el navegador no conoce. */

(function (global) {
  const CONFIG = Object.assign(
    {
      gatewayUrl: "http://localhost:8000",
      clientToken: "student-token-123",
    },
    global.CHOCO_CONFIG || {}
  );

  const API_BASE = `${CONFIG.gatewayUrl.replace(/\/$/, "")}/api`;
  const REQUEST_TIMEOUT_MS = 2500;

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

  // Origen de los últimos datos cargados: "gateway" o "respaldo".
  let origenDatos = null;

  async function gatewayRequest(path) {
    if (!global.fetch) return null;
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);
    try {
      const res = await fetch(`${API_BASE}${path}`, {
        method: "GET",
        headers: { Authorization: `Bearer ${CONFIG.clientToken}` },
        signal: controller.signal,
      });
      if (res.status === 401) {
        console.warn("[ChocoAPI] El Gateway rechazó el token (401). ¿Se rotó en Vault?");
        return null;
      }
      if (!res.ok) {
        console.warn(`[ChocoAPI] El Gateway respondió ${res.status} en ${path}.`);
        return null;
      }
      return await res.json();
    } catch (err) {
      return null;
    } finally {
      clearTimeout(timer);
    }
  }

  let cache = null;

  function respaldoLocal() {
    // Cada página .php declara su propio arreglo de productos en PHP y lo
    // vuelca a JS con json_encode. Si la página lo define, se usa ese
    // respaldo; si no, se cae al arreglo fijo de este archivo.
    const inyectado = global.CHOCO_DEMO_PRODUCTS;
    return Array.isArray(inyectado) && inyectado.length ? inyectado : DEMO_PRODUCTS;
  }

  async function fetchProductos() {
    if (cache) return cache;
    const data = await gatewayRequest("/products");
    const desdeGateway = data && Array.isArray(data.products) && data.products.length;
    origenDatos = desdeGateway ? "gateway" : "respaldo";
    console.info(
      desdeGateway
        ? `[ChocoAPI] Catálogo cargado vía API Gateway (${CONFIG.gatewayUrl}).`
        : "[ChocoAPI] Gateway no disponible: usando catálogo de respaldo."
    );
    cache = (desdeGateway ? data.products : respaldoLocal()).map(tagCategoria);
    return cache;
  }

  async function fetchProducto(id) {
    if (!id) return null;
    const data = await gatewayRequest(`/products/${encodeURIComponent(id)}`);
    if (data && data.product) {
      origenDatos = "gateway";
      return tagCategoria(data.product);
    }
    const todos = await fetchProductos();
    return todos.find((p) => p.id === String(id)) || null;
  }

  function formatCLP(numero) {
    const valor = Math.round(Number(numero) || 0);
    return "$" + valor.toLocaleString("es-CL");
  }

  global.ChocoAPI = {
    fetchProductos,
    fetchProducto,
    formatCLP,
    get origenDatos() {
      return origenDatos;
    },
  };
})(window);
