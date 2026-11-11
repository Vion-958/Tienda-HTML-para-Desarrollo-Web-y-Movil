<?php
// Mi cuenta. La sesion la maneja el API Gateway con una cookie HttpOnly.
$anio = date("Y");
?>
<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<title>ChocoMan&iacute;a &mdash; Mi cuenta</title>
<meta name="description" content="Inicia sesi&oacute;n en ChocoMan&iacute;a para ver tus pedidos.">
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

  <!-- Sin sesi&oacute;n: formulario de login -->
  <section id="loginSection" class="mt-lg" hidden>
    <div class="account-narrow">
      <div class="panel-title"><h2>Iniciar sesi&oacute;n</h2></div>
      <div class="panel-body">
        <form id="loginForm" novalidate>
          <div class="field">
            <label for="username">Usuario</label>
            <input class="field-input" id="username" name="username" type="text" autocomplete="username" required>
          </div>
          <div class="field" style="margin-top:18px;">
            <label for="password">Contrase&ntilde;a</label>
            <input class="field-input" id="password" name="password" type="password" autocomplete="current-password" required>
          </div>
          <div style="margin-top:20px; display:flex; justify-content:flex-end;">
            <button type="submit" class="btn btn--accent btn--pill" id="loginBtn">Ingresar</button>
          </div>
          <p id="loginMsg" class="account-msg" role="alert" hidden></p>
        </form>
        <p class="form-note" style="margin:18px 0 0;">
          &iquest;No tienes cuenta? <button type="button" class="link-btn" id="showRegister">Crear una cuenta</button>
        </p>
      </div>
    </div>
  </section>

  <!-- Registro de cliente -->
  <section id="registerSection" class="mt-lg" hidden>
    <div class="account-narrow">
      <div class="panel-title"><h2>Crear cuenta</h2></div>
      <div class="panel-body">
        <form id="registerForm" novalidate>
          <div class="field">
            <label for="regUsuario">Usuario *</label>
            <input class="field-input" id="regUsuario" type="text" autocomplete="username" maxlength="30" required>
            <p class="field-error" data-reg-error="username" hidden></p>
          </div>
          <div class="field" style="margin-top:14px;">
            <label for="regClave">Contrase&ntilde;a *</label>
            <input class="field-input" id="regClave" type="password" autocomplete="new-password" maxlength="72" required>
            <p class="field-hint">M&iacute;nimo 8 caracteres, con letras y n&uacute;meros.</p>
            <p class="field-error" data-reg-error="password" hidden></p>
          </div>
          <div class="field" style="margin-top:14px;">
            <label for="regNombre">Nombre completo *</label>
            <input class="field-input" id="regNombre" type="text" autocomplete="name" maxlength="80" required>
          </div>
          <div class="field" style="margin-top:14px;">
            <label for="regCorreo">Correo *</label>
            <input class="field-input" id="regCorreo" type="email" autocomplete="email" maxlength="254" required>
          </div>
          <div style="margin-top:20px; display:flex; justify-content:space-between; gap:12px;">
            <button type="button" class="btn btn--ghost btn--pill" id="showLogin">Ya tengo cuenta</button>
            <button type="submit" class="btn btn--accent btn--pill" id="registerBtn">Crear cuenta</button>
          </div>
          <p id="registerMsg" class="account-msg" role="alert" hidden></p>
        </form>
      </div>
    </div>
  </section>

  <!-- Con sesi&oacute;n: datos del usuario, pedidos y administraci&oacute;n -->
  <section id="accountSection" class="mt-lg" hidden>
    <div class="account-head">
      <div>
        <h1 class="account-title">Hola, <span id="accountName"></span></h1>
        <p style="margin:6px 0 0;">
          <span id="accountTipo"></span>
        </p>
      </div>
      <button type="button" class="btn btn--ghost btn--pill" id="logoutBtn">Cerrar sesi&oacute;n</button>
    </div>

    <div class="mt-lg">
      <div class="panel-title"><h2>Mis pedidos</h2></div>
      <div class="panel-body">
        <p id="orderActionMsg" class="account-msg" role="status" aria-live="polite" hidden></p>
        <p id="ordersMsg" class="form-note" style="margin:0;">Cargando pedidos&hellip;</p>
        <div class="account-table-wrap">
          <table class="account-table" id="ordersTable" hidden>
            <thead><tr><th>N&deg;</th><th>Fecha</th><th>Productos</th><th>Entrega</th><th>Estado</th><th>Pago</th><th>Total</th><th><span class="visually-hidden">Acciones</span></th></tr></thead>
            <tbody></tbody>
          </table>
        </div>
      </div>
    </div>

    <div class="mt-lg">
      <div class="panel-title"><h2>Mis datos</h2></div>
      <div class="panel-body">
        <form id="profileForm" class="product-form__grid" novalidate>
          <div class="field">
            <label for="pNombre">Nombre completo *</label>
            <input class="field-input" id="pNombre" type="text" maxlength="80" required>
          </div>
          <div class="field">
            <label for="pCorreo">Correo *</label>
            <input class="field-input" id="pCorreo" type="email" maxlength="254" required>
          </div>
          <div class="field">
            <label for="pTelefono">Tel&eacute;fono</label>
            <input class="field-input" id="pTelefono" type="tel" maxlength="20" placeholder="+56 9 1234 5678">
          </div>
          <div class="field">
            <label for="pComuna">Comuna</label>
            <input class="field-input" id="pComuna" type="text" maxlength="50">
          </div>
          <div class="field product-form__wide">
            <label for="pDireccion">Direcci&oacute;n de despacho</label>
            <input class="field-input" id="pDireccion" type="text" maxlength="150">
          </div>
          <div class="product-form__wide" style="display:flex; justify-content:flex-end; align-items:center; gap:14px;">
            <p id="profileMsg" class="account-msg" role="status" hidden style="margin:0;"></p>
            <button type="submit" class="btn btn--accent btn--pill" id="profileBtn">Guardar mis datos</button>
          </div>
        </form>
      </div>
    </div>

    <!-- Solo admin: cotizaciones y mensajes de contacto -->
    <div class="mt-lg" id="adminRequestsSection" hidden>
      <div class="panel-title"><h2>Solicitudes de clientes</h2></div>
      <div class="panel-body">
        <p id="adminRequestsMsg" class="account-msg" role="status" aria-live="polite" hidden></p>
        <div class="account-table-wrap">
          <table class="account-table" id="adminRequestsTable">
            <thead><tr><th>N&deg;</th><th>Tipo</th><th>Contacto</th><th>Asunto</th><th>Detalle</th><th>Estado</th><th><span class="visually-hidden">Acciones</span></th></tr></thead>
            <tbody></tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- Solo admin: pedidos de todos los clientes -->
    <div class="mt-lg" id="adminOrdersSection" hidden>
      <div class="panel-title"><h2>Gesti&oacute;n de pedidos</h2></div>
      <div class="panel-body">
        <div class="admin-toolbar" style="justify-content:flex-start; gap:10px; align-items:center;">
          <label for="adminEstado" style="font-weight:800;">Estado</label>
          <select id="adminEstado" class="field-input" style="max-width:240px;">
            <option value="">Todos</option>
            <option value="pendiente_pago">Pendiente de pago</option>
            <option value="pagado">Pagado</option>
            <option value="en_preparacion">En preparaci&oacute;n</option>
            <option value="listo_retiro">Listo para retiro</option>
            <option value="despachado">Despachado</option>
            <option value="entregado">Entregado</option>
            <option value="cancelado">Cancelado</option>
          </select>
        </div>
        <p id="adminOrdersMsg" class="account-msg" role="status" aria-live="polite" hidden></p>
        <div class="account-table-wrap">
          <table class="account-table" id="adminOrdersTable">
            <thead><tr><th>N&deg;</th><th>Cliente</th><th>Productos</th><th>Entrega</th><th>Estado</th><th>Pago</th><th>Total</th><th><span class="visually-hidden">Acciones</span></th></tr></thead>
            <tbody></tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- Solo para el rol admin. El Backend igual verifica el rol al eliminar. -->
    <div class="mt-lg" id="adminSection" hidden>
      <div class="panel-title"><h2>Administraci&oacute;n de productos</h2></div>
      <div class="panel-body">
        <div class="admin-toolbar">
          <button type="button" class="btn btn--accent btn--pill" id="toggleProductForm" aria-expanded="false" aria-controls="productForm">
            + Agregar producto
          </button>
        </div>

        <!-- Nuevo producto: se env&iacute;a como multipart/form-data al Gateway -->
        <form id="productForm" class="product-form" novalidate hidden>
          <h3 class="product-form__title" id="productFormTitle">Nuevo producto</h3>
          <p id="productFormMsg" class="account-msg" role="alert" hidden></p>

          <div class="product-form__grid">
            <div class="field">
              <label for="pfNombre">Nombre *</label>
              <input class="field-input" id="pfNombre" name="nombre" type="text" maxlength="80" required>
              <p class="field-error" data-error-for="nombre" hidden></p>
            </div>

            <div class="field">
              <label for="pfCategoria">Categor&iacute;a *</label>
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
              <label for="pfDescripcion">Descripci&oacute;n *</label>
              <textarea class="field-input" id="pfDescripcion" name="descripcion" maxlength="500" required></textarea>
              <p class="field-hint"><span id="pfDescripcionCount">0</span>/500 &CenterDot; m&iacute;nimo 10 caracteres</p>
              <p class="field-error" data-error-for="descripcion" hidden></p>
            </div>

            <div class="field product-form__wide">
              <label for="pfTags">Tags para filtros</label>
              <input class="field-input" id="pfTags" name="tags" type="text" placeholder="para regalar, sin gluten, cumplea&ntilde;os">
              <p class="field-hint">Sep&aacute;ralos con coma. Hasta 8. Aparecen como filtros en el cat&aacute;logo.</p>
              <div class="tag-chips" id="pfTagsPreview" aria-live="polite"></div>
              <p class="field-error" data-error-for="tags" hidden></p>
            </div>

            <div class="field product-form__wide">
              <label for="pfIngredientes">Ingredientes</label>
              <textarea class="field-input field-input--short" id="pfIngredientes" name="ingredientes" maxlength="300" placeholder="Chocolate 70% cacao, mantequilla, az&uacute;car rubia&hellip;"></textarea>
              <p class="field-error" data-error-for="ingredientes" hidden></p>
            </div>

            <fieldset class="field product-form__wide checkbox-group">
              <legend>Al&eacute;rgenos</legend>
              <label><input type="checkbox" name="alergenos" value="gluten"> Gluten</label>
              <label><input type="checkbox" name="alergenos" value="l&aacute;cteos"> L&aacute;cteos</label>
              <label><input type="checkbox" name="alergenos" value="huevo"> Huevo</label>
              <label><input type="checkbox" name="alergenos" value="frutos secos"> Frutos secos</label>
              <label><input type="checkbox" name="alergenos" value="soya"> Soya</label>
              <p class="field-error" data-error-for="alergenos" hidden></p>
            </fieldset>

            <div class="field product-form__wide">
              <label for="pfImagenes">Im&aacute;genes *</label>
              <input class="field-input field-input--file" id="pfImagenes" type="file" accept="image/jpeg,image/png,image/webp" multiple>
              <p class="field-hint" id="pfImagenesHint">De 1 a 5 im&aacute;genes JPG, PNG o WEBP, de hasta 2 MB cada una. La primera es la portada.</p>
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
            <thead><tr><th><span class="visually-hidden">Imagen</span></th><th>C&oacute;digo</th><th>Producto</th><th>Categor&iacute;a</th><th>Stock</th><th>Precio</th><th><span class="visually-hidden">Acciones</span></th></tr></thead>
            <tbody></tbody>
          </table>
        </div>
      </div>
    </div>
  </section>

  <p id="accountLoading" class="mt-lg" style="font-weight:700;">Revisando tu sesi&oacute;n&hellip;</p>

</main>

<footer class="site-footer">
  ChocoMan&iacute;a &copy; <?php echo htmlspecialchars($anio); ?> &CenterDot; +56 9 1234 5678 &CenterDot; chocoatencion@chocomania.cl
</footer>

<script src="js/cart.js"></script>
<script src="js/api.js"></script>
<script src="js/common.js"></script>
<script src="js/cuenta.js"></script>
</body>
</html>
