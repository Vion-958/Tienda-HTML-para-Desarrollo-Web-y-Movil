<?php
// Catálogo: la fuente real de productos es el backend GraphQL de la
// Semana 6 (mercurius + MongoDB, ver ../chocomania-graphql). Como esta
// carpeta es SOLO frontend y ese servidor no siempre está disponible
// (o el navegador bloquea la petición cross-origin porque el backend no
// declara CORS), se usa aquí el mismo catálogo de respaldo que
// data/productos.php define a partir de seed.js, y se vuelca a JS con
// json_encode. js/api.js intenta primero GraphQL y, si falla, usa este
// respaldo: la página funciona igual de navegable con o sin el servidor
// corriendo.
$productosFallback = require __DIR__ . "/data/productos.php";
$anio = date("Y");
?>
<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<title>ChocoManía — Catálogo</title>
<meta name="description" content="Catálogo de tortas, pastelería y chocolatería artesanal ChocoManía.">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="img/logo.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Dancing+Script:wght@600;700&family=Lora:wght@500;600;700&family=Nunito+Sans:wght@400;600;700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="css/styles.css">
<script>window.CHOCO_DEMO_PRODUCTS = <?php echo json_encode($productosFallback, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES); ?>;</script>
</head>
<body data-page="catalogo">
<a class="skip-link" href="#contenido">Saltar al contenido</a>

<header class="site-header">
  <div class="header-bar container">
    <a class="brand" href="index.php" aria-label="ChocoManía, ir al inicio">
      <img src="img/logo.png" alt="ChocoManía">
    </a>
    <button class="nav-toggle" type="button" aria-expanded="false" aria-controls="siteNav" aria-label="Abrir menú">
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M3 6h18M3 12h18M3 18h18"/></svg>
    </button>
    <nav id="siteNav" class="site-nav" aria-label="Principal">
      <a href="empresa.php" data-page="empresa">Sobre Nosotros</a>
      <a href="catalogo.php" data-page="catalogo">Catálogo</a>
      <a href="index.php" data-page="pedidos">Pedidos Especiales</a>
    </nav>
    <form class="search-form" role="search" action="catalogo.php" method="get">
      <label for="buscar" class="visually-hidden">Buscar producto</label>
      <input id="buscar" name="q" type="search" placeholder="Buscar producto" autocomplete="off">
      <button type="submit" aria-label="Buscar">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"><circle cx="10" cy="10" r="6.5"/><path d="M15 15 L21 21"/></svg>
      </button>
    </form>
    <a class="cart-link" href="carrito.php" aria-label="Ver carrito">
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#ffffff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 3 H5 L7.5 15 H18.5 L21 7 H6"/><circle cx="9" cy="19.5" r="1.5"/><circle cx="17" cy="19.5" r="1.5"/></svg>
      <span class="cart-badge" data-cart-badge>0</span>
    </a>
  </div>
</header>

<main id="contenido" class="container">
  <div class="catalog-layout">

    <aside class="catalog-sidebar">
      <div class="panel">
        <div class="panel-title"><h2>Categorías</h2></div>
        <div class="panel-body">
          <div class="category-list" id="categoryList" role="group" aria-label="Filtrar por categoría"></div>
        </div>
      </div>

      <div class="panel mini-cart-panel">
        <div class="panel-title"><h2>Carrito</h2></div>
        <div class="panel-body mini-cart" id="miniCart"></div>
        <a href="carrito.php" class="btn btn--accent btn--block" style="border-radius:0;">Pagar</a>
      </div>
    </aside>

    <section class="catalog-main">
      <p id="catalogStatus" aria-live="polite" style="margin:0 0 16px; font-weight:700;">Cargando productos…</p>
      <div class="grid grid--3" id="productGrid"></div>
      <nav class="pagination" id="pagination" aria-label="Páginas de resultados" hidden>
        <button type="button" id="prevPage" aria-label="Página anterior">‹</button>
        <span id="pageIndicator" aria-live="polite">1</span>
        <button type="button" id="nextPage" aria-label="Página siguiente">›</button>
      </nav>
    </section>

    <aside class="catalog-offers">
      <div class="section-title"><h2 style="font-size:22px;">Ofertas</h2></div>
      <div id="offerSlot"></div>
    </aside>

  </div>
</main>

<footer class="site-footer">
  ChocoManía © <?php echo htmlspecialchars($anio); ?> · +56 9 1234 5678 · chocoatencion@chocomania.cl
</footer>

<script src="js/cart.js"></script>
<script src="js/api.js"></script>
<script src="js/common.js"></script>
<script src="js/catalogo.js"></script>
</body>
</html>
