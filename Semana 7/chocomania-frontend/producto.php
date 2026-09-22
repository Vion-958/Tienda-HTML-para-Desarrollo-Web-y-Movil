<?php
// Detalle de producto. El id llega por GET (?id=...), tal como en los
// productos.php de la clase. PHP solo valida y sanea ese parámetro antes
// de imprimirlo; la carga real del producto (contra GraphQL o el
// catálogo de respaldo) ocurre en el navegador, en js/producto.js.
$productosFallback = require __DIR__ . "/data/productos.php";
$idProducto = isset($_GET["id"]) ? substr(preg_replace("/[^a-zA-Z0-9_-]/", "", $_GET["id"]), 0, 64) : "";
$anio = date("Y");
?>
<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<title>ChocoManía — Producto</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="img/logo.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Dancing+Script:wght@600;700&family=Lora:wght@500;600;700&family=Nunito+Sans:wght@400;600;700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="css/styles.css">
<script>
  window.CHOCO_DEMO_PRODUCTS = <?php echo json_encode($productosFallback, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES); ?>;
  window.CHOCO_PRODUCT_ID = <?php echo json_encode($idProducto, JSON_UNESCAPED_UNICODE); ?>;
</script>
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

  <nav class="breadcrumb" aria-label="Ruta de navegación">
    <a href="catalogo.php">Catálogo</a>
    <span aria-hidden="true">›</span>
    <span id="breadcrumbCurrent" aria-current="page">Cargando…</span>
  </nav>

  <div id="productRoot">
    <p style="font-weight:700;">Cargando producto…</p>
  </div>

  <section class="mt-lg" id="relatedSection" hidden>
    <h2 style="margin-bottom:20px;">También te puede gustar</h2>
    <div class="grid grid--4" id="relatedGrid"></div>
  </section>

</main>

<footer class="site-footer">
  ChocoManía © <?php echo htmlspecialchars($anio); ?> · +56 9 1234 5678 · chocoatencion@chocomania.cl
</footer>

<script src="js/cart.js"></script>
<script src="js/api.js"></script>
<script src="js/common.js"></script>
<script src="js/producto.js"></script>
</body>
</html>
