/* ChocoManía — capa de datos.
   Intenta leer del backend GraphQL (Semana 6, mercurius + MongoDB) en
   http://localhost:4000/graphql. Si el servidor no está corriendo, no
   está en la misma máquina, o el navegador bloquea la petición por CORS
   (el backend de la clase no declara cabeceras CORS), se usa un catálogo
   de respaldo con los mismos productos que carga seed.js, para que el
   sitio siga siendo 100% navegable de forma independiente. */

(function (global) {
  const API_URL = "http://localhost:4000/graphql";
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
  // "categoria" propia (por ejemplo, si algún día vienen del backend
  // GraphQL, que hoy no expone ese campo).
  const CATEGORY_RULES = [
    { categoria: "Vegana", test: /vegan/i },
    { categoria: "Sin azúcar", test: /sin azúcar|stevia|maltitol/i },
    { categoria: "Por mayor", test: /por mayor|al por mayor/i },
    { categoria: "De leche", test: /torta|leches|cumplea|alfajor/i },
    { categoria: "Postres", test: /brownie|cupcake|pie|croissant|pastel/i },
    { categoria: "Amargo", test: /70%|85%|amargo|cacao/i },
  ];

  function tagCategoria(producto) {
    if (producto.categoria) return producto;
    const texto = `${producto.nombre} ${producto.descripcion || ""}`;
    const regla = CATEGORY_RULES.find((r) => r.test.test(texto));
    return { ...producto, categoria: regla ? regla.categoria : "Otros" };
  }

  async function graphqlRequest(query, variables) {
    if (!global.fetch) return null;
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);
    try {
      const res = await fetch(API_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query, variables }),
        signal: controller.signal,
      });
      if (!res.ok) return null;
      const json = await res.json();
      if (json.errors || !json.data) return null;
      return json.data;
    } catch (err) {
      return null;
    } finally {
      clearTimeout(timer);
    }
  }

  let cache = null;

  function respaldoLocal() {
    // Cada página .php declara su propio arreglo de productos en PHP y lo
    // vuelca a JS con json_encode (mismo patrón que productos.php de la
    // clase). Si la página lo define, se usa ese respaldo; si no, se cae
    // al arreglo fijo de este archivo.
    const inyectado = global.CHOCO_DEMO_PRODUCTS;
    return Array.isArray(inyectado) && inyectado.length ? inyectado : DEMO_PRODUCTS;
  }

  async function fetchProductos() {
    if (cache) return cache;
    const data = await graphqlRequest(
      "query { productos { id nombre precio descripcion imagen } }"
    );
    const lista =
      data && Array.isArray(data.productos) && data.productos.length
        ? data.productos
        : respaldoLocal();
    cache = lista.map(tagCategoria);
    return cache;
  }

  async function fetchProducto(id) {
    if (!id) return null;
    const data = await graphqlRequest(
      "query($id: ID!) { producto(id: $id) { id nombre precio descripcion imagen } }",
      { id }
    );
    if (data && data.producto) return tagCategoria(data.producto);
    const todos = await fetchProductos();
    return todos.find((p) => p.id === id) || null;
  }

  function formatCLP(numero) {
    const valor = Math.round(Number(numero) || 0);
    return "$" + valor.toLocaleString("es-CL");
  }

  global.ChocoAPI = {
    fetchProductos,
    fetchProducto,
    formatCLP,
  };
})(window);
