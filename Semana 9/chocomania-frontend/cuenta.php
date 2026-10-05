<?php
// Mi cuenta: login, usuario actual, pedidos, administración y logout.
// PHP no maneja la sesión: todo pasa por el API Gateway (/auth/*, /api/*),
// que guarda el token en una cookie HttpOnly. js/cuenta.js arma la página
// según lo que responda el Gateway.
$anio = date("Y");
?>
<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<title>ChocoManía — Mi cuenta</title>
<meta name="description" content="Inicia sesión en ChocoManía para ver tus pedidos.">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="img/logo.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Dancing+Script:wght@600;700&family=Lora:wght@500;600;700&family=Nunito+Sans:wght@400;600;700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="css/styles.css">
</head>
<body data-page="cuenta">
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

  <!-- Sin sesión: formulario de login -->
  <section id="loginSection" class="mt-lg" hidden>
    <div class="account-narrow">
      <div class="panel-title"><h2>Iniciar sesión</h2></div>
      <div class="panel-body">
        <form id="loginForm" novalidate>
          <div class="field">
            <label for="username">Usuario</label>
            <input class="field-input" id="username" name="username" type="text" autocomplete="username" required>
          </div>
          <div class="field" style="margin-top:18px;">
            <label for="password">Contraseña</label>
            <input class="field-input" id="password" name="password" type="password" autocomplete="current-password" required>
          </div>
          <div style="margin-top:20px; display:flex; justify-content:flex-end;">
            <button type="submit" class="btn btn--accent btn--pill" id="loginBtn">Ingresar</button>
          </div>
          <p id="loginMsg" class="account-msg" role="alert" hidden></p>
        </form>
        <p class="form-note" style="margin:18px 0 0;">
          Usuarios de prueba del laboratorio: <strong>ana / 1234</strong> (cliente) y
          <strong>ernesto / admin123</strong> (administrador).
        </p>
      </div>
    </div>
  </section>

  <!-- Con sesión: datos del usuario, pedidos y administración -->
  <section id="accountSection" class="mt-lg" hidden>
    <div class="account-head">
      <div>
        <h1 class="account-title">Hola, <span id="accountName"></span></h1>
        <p style="margin:6px 0 0;">
          Usuario <strong id="accountId"></strong> · Roles: <span id="accountRoles"></span>
        </p>
      </div>
      <button type="button" class="btn btn--ghost btn--pill" id="logoutBtn">Cerrar sesión</button>
    </div>

    <div class="detail-grid mt-lg" style="align-items:flex-start;">
      <div style="grid-column: span 2;">
        <div class="panel-title"><h2>Mis pedidos</h2></div>
        <div class="panel-body">
          <p id="ordersMsg" class="form-note" style="margin:0;">Cargando pedidos…</p>
          <div class="account-table-wrap">
            <table class="account-table" id="ordersTable" hidden>
              <thead><tr><th>N°</th><th>Cliente</th><th>Estado</th><th>Productos</th><th>Total</th></tr></thead>
              <tbody></tbody>
            </table>
          </div>
        </div>
      </div>

      <div>
        <div class="panel-title"><h2>Cómo funciona</h2></div>
        <div class="panel-body form-note">
          <p style="margin:0 0 10px;">Tu sesión vive en una cookie <strong>HttpOnly</strong>: este sitio no puede leer el token.</p>
          <p style="margin:0;">Cada solicitud pasa por el API Gateway, que valida la sesión con el Auth Service y revisa tus roles antes de llegar al backend.</p>
        </div>
      </div>
    </div>

    <div class="mt-lg">
      <div class="panel-title"><h2>Administración de productos</h2></div>
      <div class="panel-body">
        <p class="form-note" style="margin:0 0 14px;">
          Eliminar un producto requiere el rol <strong>admin</strong>. El botón se muestra a todos a
          propósito: quien decide es el servidor, no la página.
        </p>
        <p id="adminMsg" class="account-msg" role="status" aria-live="polite" hidden></p>
        <div class="account-table-wrap">
          <table class="account-table" id="productsTable">
            <thead><tr><th>Código</th><th>Producto</th><th>Precio</th><th><span class="visually-hidden">Acciones</span></th></tr></thead>
            <tbody></tbody>
          </table>
        </div>
      </div>
    </div>
  </section>

  <p id="accountLoading" class="mt-lg" style="font-weight:700;">Revisando tu sesión…</p>

</main>

<footer class="site-footer">
  ChocoManía © <?php echo htmlspecialchars($anio); ?> · +56 9 1234 5678 · chocoatencion@chocomania.cl
</footer>

<script src="js/cart.js"></script>
<script src="js/api.js"></script>
<script src="js/common.js"></script>
<script src="js/cuenta.js"></script>
</body>
</html>
