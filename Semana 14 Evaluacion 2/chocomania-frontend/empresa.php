<?php
// Sobre Nosotros: mision, equipo y contacto.
$anio = date("Y");
?>
<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<title>ChocoMan&iacute;a &mdash; Sobre Nosotros</title>
<meta name="description" content="Conoce ChocoMan&iacute;a: chocolater&iacute;a artesanal, nuestro equipo y c&oacute;mo contactarnos.">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="img/logo.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Dancing+Script:wght@600;700&family=Lora:wght@500;600;700&family=Nunito+Sans:wght@400;600;700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="css/styles.css">
</head>
<body data-page="empresa">
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

  <section class="mt-lg">
    <div class="detail-grid" style="align-items:flex-start;">

      <div>
        <div class="hero__media" style="margin:0 auto 24px;">
          <img src="img/hero-empresa.jpg" alt="Equipo ChocoMan&iacute;a elaborando chocolate artesanal">
        </div>
        <div class="panel-title"><h2>Informaci&oacute;n contacto</h2></div>
        <div class="panel-body">
          <div>Tel&eacute;fono: <a href="tel:+56912345678" style="color:inherit;">+56 9 1234 5678</a></div>
          <div>Correo: <a href="mailto:chocoatencion@chocomania.cl" style="color:inherit;">chocoatencion@chocomania.cl</a></div>
        </div>
      </div>

      <div style="grid-column: span 2;">
        <div class="panel-title"><h2>Nuestra misi&oacute;n</h2></div>
        <div class="panel-body">
          <p style="margin:0;">ChocoMan&iacute;a es una chocolater&iacute;a artesanal dedicada a crear chocolates de autor, hechos a mano en peque&ntilde;os lotes. Nacimos en 2014 con la idea de acercar la pasteler&iacute;a fina a cada celebraci&oacute;n, cuidando cada receta desde el ingrediente hasta el empaque.</p>
        </div>

        <div class="panel-title mt-lg" style="margin-top:24px;"><h2>Qui&eacute;nes somos</h2></div>
        <div class="panel-body">
          <p style="margin:0;">Ubicados en Av. Providencia 1234, Providencia, trabajamos con proveedores locales de cacao y fruta de estaci&oacute;n para ofrecer tortas, pasteler&iacute;a y chocolater&iacute;a fresca todos los d&iacute;as.</p>
        </div>
      </div>

    </div>
  </section>

  <section class="mt-lg">
    <div class="section-title">
      <div class="panel-title" style="max-width:520px;">
        <h2>Nuestro equipo</h2>
      </div>
    </div>
    <div class="grid grid--2" style="max-width:620px; margin:0 auto;">

      <div class="team-card">
        <div class="team-card__media" aria-hidden="true">
          <svg width="100%" height="100%" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.3" style="padding:22px; color:#9a6d3d;"><circle cx="12" cy="8" r="4"/><path d="M4 20c0-4.4 3.6-8 8-8s8 3.6 8 8"/></svg>
        </div>
        <h3 style="font-size:17px;">Mar&iacute;a Jos&eacute;</h3>
        <p style="margin:0;">Chocolatera jefe</p>
      </div>

      <div class="team-card">
        <div class="team-card__media">
          <img src="img/team-tomas.jpg" alt="Tom&aacute;s, maestro chocolatero de ChocoMan&iacute;a">
        </div>
        <h3 style="font-size:17px;">Tom&aacute;s</h3>
        <p style="margin:0;">Maestro chocolatero</p>
      </div>

    </div>
  </section>

  <section class="mt-lg">
    <div class="detail-grid">

      <div style="grid-column: span 2;">
        <div class="panel-title"><h2>Contacto</h2></div>
        <div class="panel-body">
          <form id="contactUsForm" novalidate>
            <div class="field">
              <label for="emailContacto">Email</label>
              <input class="field-input" id="emailContacto" name="emailContacto" type="email" placeholder="tucorreo@ejemplo.cl" required>
            </div>
            <div class="field" style="margin-top:18px;">
              <label for="comentarios">Comentarios</label>
              <textarea class="field-input" id="comentarios" name="comentarios" placeholder="Cu&eacute;ntanos en qu&eacute; te podemos ayudar&hellip;" required></textarea>
            </div>
            <div class="field" style="margin-top:18px;">
              <label for="motivo">Motivo de contacto</label>
              <select class="field-input" id="motivo" name="motivo">
                <option>Consulta por pedido</option>
                <option>Reclamo</option>
                <option>Sugerencia</option>
                <option>Trabaja con nosotros</option>
              </select>
            </div>
            <div style="margin-top:20px; display:flex; justify-content:flex-end;">
              <button type="submit" class="btn btn--accent btn--pill">Enviar</button>
            </div>
            <p id="contactUsMsg" role="status" aria-live="polite" style="margin:14px 0 0; font-weight:800; display:none;"></p>
          </form>
        </div>
      </div>

      <div>
        <div class="panel-title"><h2>Ub&iacute;canos</h2></div>
        <div class="panel-body">
          <p style="margin:0 0 10px;">Av. Providencia 1234, Providencia, Santiago</p>
          <p style="margin:0 0 10px;"><strong>Horario:</strong> Lunes a s&aacute;bado, 9:00 a 20:00</p>
          <p style="margin:0;">Retiro en tienda o delivery: revisa nuestros <a href="index.php" style="color:inherit; font-weight:700;">Pedidos Especiales</a>.</p>
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
<script src="js/empresa.js"></script>
</body>
</html>
