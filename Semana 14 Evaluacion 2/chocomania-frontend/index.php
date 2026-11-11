<?php
// Inicio: Pedidos Especiales.
$anio = date("Y");
?>
<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<title>ChocoMan&iacute;a &mdash; Pedidos Especiales</title>
<meta name="description" content="ChocoMan&iacute;a: chocolater&iacute;a artesanal. Pedidos especiales, tortas por encargo y regalos corporativos hechos a mano.">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="img/logo.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Dancing+Script:wght@600;700&family=Lora:wght@500;600;700&family=Nunito+Sans:wght@400;600;700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="css/styles.css">
</head>
<body data-page="pedidos">
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

  <section class="hero panel">
    <div class="hero__media">
      <img src="img/hero-pedidos.jpg" alt="Chocolate artesanal ChocoMan&iacute;a hecho a mano">
    </div>
    <div class="hero__content">
      <div class="panel-title">
        <h1>Pedidos Especiales</h1>
      </div>
      <div class="panel-body">
        <p>Chocolates y dulces hechos a tu medida para cumplea&ntilde;os, matrimonios, regalos y eventos de empresa. Cu&eacute;ntanos tu idea y la hacemos realidad.</p>
        <ul>
          <li>Hechos a mano, en peque&ntilde;os lotes</li>
          <li>Dise&ntilde;o a tu gusto: mensaje, color y formato</li>
          <li>Te respondemos con una cotizaci&oacute;n</li>
        </ul>
      </div>
    </div>
  </section>

  <section class="mt-lg">
    <div class="section-title">
      <div class="panel-title" style="max-width:520px;">
        <h2>Nuestros servicios</h2>
      </div>
    </div>
    <div class="grid grid--3" id="serviciosGrid"></div>
  </section>

  <section class="mt-lg" id="cotizar">
    <div class="detail-grid" style="align-items:flex-start;">

      <div>
        <div class="panel-title"><h2>&iquest;C&oacute;mo pedir?</h2></div>
        <div class="panel-body">
          <ol class="steps">
            <li><span class="step-number">1</span><span><strong>Cu&eacute;ntanos tu idea.</strong> Completa el formulario con fecha, cantidad y detalles.</span></li>
            <li><span class="step-number">2</span><span><strong>Recibe tu cotizaci&oacute;n.</strong> Te contactamos por correo o tel&eacute;fono.</span></li>
            <li><span class="step-number">3</span><span><strong>Confirma y disfruta.</strong> Coordinamos retiro en tienda o delivery.</span></li>
          </ol>
        </div>

        <div class="panel-title mt-lg" style="margin-top:24px;"><h2>Informaci&oacute;n contacto</h2></div>
        <div class="panel-body">
          <div>Tel&eacute;fono: <a href="tel:+56912345678" style="color:inherit;">+56 9 1234 5678</a></div>
          <div>Correo: <a href="mailto:chocoatencion@chocomania.cl" style="color:inherit;">chocoatencion@chocomania.cl</a></div>
        </div>
      </div>

      <div style="grid-column: span 2;">
        <div class="panel-title"><h2>Solicita tu cotizaci&oacute;n</h2></div>
        <div class="panel-body">
          <form id="quoteForm" novalidate>
            <div class="form-grid form-grid--2">
              <div class="field">
                <label for="nombre">Nombre</label>
                <input class="field-input" id="nombre" name="nombre" type="text" placeholder="Tu nombre" required>
              </div>
              <div class="field">
                <label for="correo">Correo</label>
                <input class="field-input" id="correo" name="correo" type="email" placeholder="tucorreo@ejemplo.cl" required>
              </div>
            </div>
            <div class="form-grid form-grid--2" style="margin-top:18px;">
              <div class="field">
                <label for="telefono">Tel&eacute;fono</label>
                <input class="field-input" id="telefono" name="telefono" type="tel" placeholder="+56 9 1234 5678">
              </div>
              <div class="field">
                <label for="tipo">Tipo de pedido</label>
                <select class="field-input" id="tipo" name="tipo">
                  <option>Chocolates personalizados</option>
                  <option>C&oacute;cteles de dulces</option>
                  <option>Delivery</option>
                  <option>Tortas por encargo</option>
                  <option>Regalos corporativos</option>
                  <option>Talleres de chocolater&iacute;a</option>
                </select>
              </div>
            </div>
            <div class="form-grid form-grid--2" style="margin-top:18px;">
              <div class="field">
                <label for="fecha">Fecha requerida</label>
                <input class="field-input" id="fecha" name="fecha" type="date">
              </div>
              <div class="field">
                <label for="cantidad">Cantidad aproximada</label>
                <input class="field-input" id="cantidad" name="cantidad" type="text" placeholder="Ej: 40 unidades">
              </div>
            </div>
            <div class="field" style="margin-top:18px;">
              <label for="detalles">Cu&eacute;ntanos tu idea</label>
              <textarea class="field-input" id="detalles" name="detalles" placeholder="Sabores, colores, mensaje, direcci&oacute;n de entrega&hellip;"></textarea>
            </div>
            <div style="margin-top:20px; display:flex; justify-content:flex-end;">
              <button type="submit" class="btn btn--accent btn--pill">Enviar solicitud</button>
            </div>
            <p id="quoteMsg" role="status" aria-live="polite" style="margin:14px 0 0; font-weight:800; display:none;"></p>
          </form>
        </div>
      </div>

    </div>
  </section>

</main>

<footer class="site-footer">
  ChocoMan&iacute;a &copy; <?php echo htmlspecialchars($anio); ?> &CenterDot; +56 9 1234 5678 &CenterDot; chocoatencion@chocomania.cl
</footer>

<script src="js/cart.js"></script>
<script src="js/api.js"></script>
<script src="js/common.js"></script>
<script src="js/main.js"></script>
</body>
</html>
