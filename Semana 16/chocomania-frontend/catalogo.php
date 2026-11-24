<?php
// Catalogo. Los productos vienen del API Gateway; si no responde se usa data/productos.php.
$productosFallback = require __DIR__ . "/data/productos.php";
$anio = date("Y");
?>
<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<title>ChocoMan&iacute;a &mdash; Cat&aacute;logo</title>
<meta name="description" content="Cat&aacute;logo de tortas, pasteler&iacute;a y chocolater&iacute;a artesanal ChocoMan&iacute;a.">
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
    <a class="brand" href="index.php" aria-label="ChocoMan&iacute;a, ir al inicio">
      <img src="img/logo.png" alt="ChocoMan&iacute;a">
    </a>
    <button class="nav-toggle" type="button" aria-expanded="false" aria-controls="siteNav" aria-label="Abrir men&uacute;">
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M3 6h18M3 12h18M3 18h18"/></svg>
    </button>
    <nav id="siteNav" class="site-nav" aria-label="Principal">
      <a href="empresa.php" data-page="empresa">Sobre Nosotros</a>
      <a href="catalogo.php" data-page="catalogo">Cat&aacute;logo</a>
      <a href="index.php" data-page="pedidos">Pedidos Especiales</a>
      <a href="cuenta.php" data-page="cuenta" data-account-link>Mi cuenta</a>
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
        <div class="panel-title"><h2>Categor&iacute;as</h2></div>
        <div class="panel-body">
          <div class="category-list" id="categoryList" role="group" aria-label="Filtrar por categor&iacute;a"></div>
        </div>
      </div>

      <div class="panel" id="tagPanel" hidden>
        <div class="panel-title"><h2>Filtrar por tags</h2></div>
        <div class="panel-body">
          <div class="tag-filter" id="tagFilter" role="group" aria-label="Filtrar por tags"></div>
        </div>
      </div>

      <div class="panel mini-cart-panel">
        <div class="panel-title"><h2>Carrito</h2></div>
        <div class="panel-body mini-cart" id="miniCart"></div>
        <a href="carrito.php" class="btn btn--accent btn--block" style="border-radius:0;">Pagar</a>
      </div>
    </aside>

    <section class="catalog-main">
      <p id="catalogStatus" aria-live="polite" style="margin:0 0 16px; font-weight:700;">Cargando productos&hellip;</p>
      <div class="grid grid--3" id="productGrid"></div>
      <nav class="pagination" id="pagination" aria-label="P&aacute;ginas de resultados" hidden>
        <button type="button" id="prevPage" aria-label="P&aacute;gina anterior">&lsaquo;</button>
        <span id="pageIndicator" aria-live="polite">1</span>
        <button type="button" id="nextPage" aria-label="P&aacute;gina siguiente">&rsaquo;</button>
      </nav>
    </section>

    <aside class="catalog-offers">
      <div class="section-title"><h2 style="font-size:22px;">Recomendado</h2></div>
      <div id="offerSlot"></div>
    </aside>

  </div>
</main>

<footer class="site-footer">
  ChocoMan&iacute;a &copy; <?php echo htmlspecialchars($anio); ?> &CenterDot; +56 9 1234 5678 &CenterDot; chocoatencion@chocomania.cl
</footer>

<script src="js/cart.js"></script>
<script src="js/api.js"></script>
<script src="js/common.js"></script>
<script src="js/catalogo.js"></script>
</body>
</html>
