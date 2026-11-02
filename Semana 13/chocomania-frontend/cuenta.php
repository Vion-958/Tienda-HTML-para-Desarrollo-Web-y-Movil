<?php
// Mi cuenta: login, usuario actual, pedidos, administración (solo admin) y logout.
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

    <div class="mt-lg">
      <div class="panel-title"><h2>Mis pedidos</h2></div>
      <div class="panel-body">
        <p id="ordersMsg" class="form-note" style="margin:0;">Cargando pedidos…</p>
        <p id="orderActionMsg" class="account-msg" role="status" aria-live="polite" hidden></p>
        <div class="account-table-wrap">
          <table class="account-table" id="ordersTable" hidden>
            <thead><tr><th>N°</th><th>Cliente</th><th>Estado</th><th>Productos</th><th>Total</th><th><span class="visually-hidden">Acciones</span></th></tr></thead>
            <tbody></tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- Solo para el rol admin. El Backend igual verifica el rol al eliminar. -->
    <div class="mt-lg" id="adminSection" hidden>
      <div class="panel-title"><h2>Administración de productos</h2></div>
      <div class="panel-body">
        <div class="admin-toolbar">
          <button type="button" class="btn btn--accent btn--pill" id="toggleProductForm" aria-expanded="false" aria-controls="productForm">
            + Agregar producto
          </button>
        </div>

        <!-- Nuevo producto: se envía como multipart/form-data al Gateway -->
        <form id="productForm" class="product-form" novalidate hidden>
          <h3 class="product-form__title">Nuevo producto</h3>
          <p id="productFormMsg" class="account-msg" role="alert" hidden></p>

          <div class="product-form__grid">
            <div class="field">
              <label for="pfNombre">Nombre *</label>
              <input class="field-input" id="pfNombre" name="nombre" type="text" maxlength="80" required>
              <p class="field-error" data-error-for="nombre" hidden></p>
            </div>

            <div class="field">
              <label for="pfCategoria">Categoría *</label>
              <input class="field-input" id="pfCategoria" name="categoria" type="text" maxlength="30" list="pfCategorias" placeholder="Elige una o escribe una nueva" required>
              <datalist id="pfCategorias"></datalist>
              <p class="field-error" data-error-for="categoria" hidden></p>
            </div>

            <div class="field">
              <label for="pfPrecio">Precio (CLP) *</label>
              <input class="field-input" id="pfPrecio" name="precio" type="number" min="100" max="10000000" step="1" inputmode="numeric" required>
              <p class="field-error" data-error-for="precio" hidden></p>
            </div>

            <div class="field">
              <label for="pfStock">Stock disponible *</label>
              <input class="field-input" id="pfStock" name="stock" type="number" min="0" max="9999" step="1" value="10" inputmode="numeric" required>
              <p class="field-error" data-error-for="stock" hidden></p>
            </div>

            <div class="field product-form__wide">
              <label for="pfDescripcion">Descripción *</label>
              <textarea class="field-input" id="pfDescripcion" name="descripcion" maxlength="500" required></textarea>
              <p class="field-hint"><span id="pfDescripcionCount">0</span>/500 · mínimo 10 caracteres</p>
              <p class="field-error" data-error-for="descripcion" hidden></p>
            </div>

            <div class="field product-form__wide">
              <label for="pfTags">Tags para filtros</label>
              <input class="field-input" id="pfTags" name="tags" type="text" placeholder="para regalar, sin gluten, cumpleaños">
              <p class="field-hint">Sepáralos con coma. Hasta 8. Aparecen como filtros en el catálogo.</p>
              <div class="tag-chips" id="pfTagsPreview" aria-live="polite"></div>
              <p class="field-error" data-error-for="tags" hidden></p>
            </div>

            <div class="field product-form__wide">
              <label for="pfIngredientes">Ingredientes</label>
              <textarea class="field-input field-input--short" id="pfIngredientes" name="ingredientes" maxlength="300" placeholder="Chocolate 70% cacao, mantequilla, azúcar rubia…"></textarea>
              <p class="field-error" data-error-for="ingredientes" hidden></p>
            </div>

            <fieldset class="field product-form__wide checkbox-group">
              <legend>Alérgenos</legend>
              <label><input type="checkbox" name="alergenos" value="gluten"> Gluten</label>
              <label><input type="checkbox" name="alergenos" value="lácteos"> Lácteos</label>
              <label><input type="checkbox" name="alergenos" value="huevo"> Huevo</label>
              <label><input type="checkbox" name="alergenos" value="frutos secos"> Frutos secos</label>
              <label><input type="checkbox" name="alergenos" value="soya"> Soya</label>
              <p class="field-error" data-error-for="alergenos" hidden></p>
            </fieldset>

            <div class="field product-form__wide">
              <label for="pfImagenes">Imágenes *</label>
              <input class="field-input field-input--file" id="pfImagenes" type="file" accept="image/jpeg,image/png,image/webp" multiple>
              <p class="field-hint">De 1 a 5 imágenes JPG, PNG o WEBP, de hasta 2 MB cada una. La primera es la portada.</p>
              <div class="image-previews" id="pfPreviews"></div>
              <p class="field-error" data-error-for="imagenes" hidden></p>
            </div>
          </div>

          <div class="product-form__actions">
            <button type="button" class="btn btn--ghost btn--pill" id="pfCancelar">Cancelar</button>
            <button type="submit" class="btn btn--accent btn--pill" id="pfGuardar">Guardar producto</button>
          </div>
        </form>

        <p id="adminMsg" class="account-msg" role="status" aria-live="polite" hidden></p>
        <div class="account-table-wrap">
          <table class="account-table" id="productsTable">
            <thead><tr><th><span class="visually-hidden">Imagen</span></th><th>Código</th><th>Producto</th><th>Categoría</th><th>Stock</th><th>Precio</th><th><span class="visually-hidden">Acciones</span></th></tr></thead>
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
