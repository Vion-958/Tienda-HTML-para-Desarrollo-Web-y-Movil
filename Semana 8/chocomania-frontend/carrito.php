<?php
// Carrito de compras. El carrito en sí vive en localStorage (window.ChocoCart,
// ver js/cart.js) porque no hay sesión de servidor en este frontend estático;
// PHP solo imprime el layout, igual que en el resto de páginas.
$anio = date("Y");
?>
<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<title>ChocoManía — Carrito</title>
<meta name="description" content="Revisa tu carrito, completa tus datos de entrega y paga tu pedido ChocoManía.">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="img/logo.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Dancing+Script:wght@600;700&family=Lora:wght@500;600;700&family=Nunito+Sans:wght@400;600;700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="css/styles.css">
</head>
<body data-page="carrito">
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
  <div class="cart-layout" id="cartLayout">

    <div class="cart-main">

      <div class="panel">
        <div class="panel-title"><h1>Tu Carrito</h1></div>
        <div class="panel-body">
          <div id="cartItems"></div>
          <p id="cartEmptyMsg" class="cart-empty" hidden>
            Tu carrito está vacío por ahora.<br>
            <a href="catalogo.php" style="color:inherit;">Ver catálogo</a>
          </p>
          <a href="catalogo.php" class="btn btn--ghost" style="margin-top:18px;">← Seguir comprando</a>
        </div>
      </div>

      <div class="panel" id="contactPanel">
        <div class="panel-title"><h2>Datos de contacto y entrega</h2></div>
        <div class="panel-body">
          <form id="contactForm" novalidate>
            <div class="form-grid form-grid--2">
              <div class="field">
                <label for="nombre">Nombre</label>
                <input class="field-input" id="nombre" name="nombre" type="text" placeholder="Tu nombre" required>
              </div>
              <div class="field">
                <label for="apellido">Apellido</label>
                <input class="field-input" id="apellido" name="apellido" type="text" placeholder="Tu apellido" required>
              </div>
            </div>
            <div class="form-grid form-grid--2" style="margin-top:18px;">
              <div class="field">
                <label for="correo">Correo</label>
                <input class="field-input" id="correo" name="correo" type="email" placeholder="tucorreo@ejemplo.cl" required>
              </div>
              <div class="field">
                <label for="telefono">Teléfono</label>
                <input class="field-input" id="telefono" name="telefono" type="tel" placeholder="+56 9 1234 5678" required>
              </div>
            </div>

            <div class="field" style="margin-top:18px;">
              <label>Método de entrega</label>
              <div class="option-group" id="deliveryGroup">
                <button type="button" class="option-btn" data-delivery="domicilio" aria-pressed="true">
                  <span class="option-btn__dot" aria-hidden="true"></span> Despacho a domicilio
                </button>
                <button type="button" class="option-btn" data-delivery="tienda" aria-pressed="false">
                  <span class="option-btn__dot" aria-hidden="true"></span> Retiro en tienda
                </button>
              </div>
              <input type="hidden" id="metodoEntrega" name="metodoEntrega" value="domicilio">
            </div>

            <div id="deliveryFields">
              <div class="form-grid form-grid--2" style="margin-top:18px;">
                <div class="field">
                  <label for="direccion">Dirección</label>
                  <input class="field-input" id="direccion" name="direccion" type="text" placeholder="Calle y número" required>
                </div>
                <div class="field">
                  <label for="comuna">Comuna</label>
                  <input class="field-input" id="comuna" name="comuna" type="text" placeholder="Tu comuna" required>
                </div>
              </div>
              <div class="form-grid form-grid--2" style="margin-top:18px;">
                <div class="field">
                  <label for="region">Región</label>
                  <input class="field-input" id="region" name="region" type="text" placeholder="Tu región" required>
                </div>
                <div class="field">
                  <label for="depto">Depto., casa o referencia</label>
                  <input class="field-input" id="depto" name="depto" type="text" placeholder="Ej: Depto 402">
                </div>
              </div>
            </div>

            <div class="field" style="margin-top:18px;">
              <label for="notas">Notas del pedido</label>
              <textarea class="field-input" id="notas" name="notas" placeholder="Mensaje para la torta, horario preferido, indicaciones de entrega…"></textarea>
            </div>
          </form>
        </div>
      </div>

    </div>

    <div class="cart-sidebar">

      <div class="panel">
        <div class="panel-title"><h2>Resumen</h2></div>
        <div class="panel-body" id="summaryBody">
          <div class="summary-row"><span>Subtotal</span><span id="sumSubtotal">$0</span></div>
          <div class="summary-row" id="sumDiscountRow" hidden><span>Descuento</span><span id="sumDiscount">-$0</span></div>
          <div class="summary-row"><span>Envío</span><span id="sumEnvio">Por calcular</span></div>
          <div class="summary-row summary-row--total" style="margin-top:8px;"><span>Total</span><strong id="sumTotal">$0</strong></div>

          <div class="field" style="margin-top:20px;">
            <label for="cupon">Código de descuento</label>
            <div class="coupon-row">
              <input class="field-input" id="cupon" name="cupon" type="text" placeholder="Ingresa tu código">
              <button type="button" class="btn btn--accent" id="aplicarCupon">Aplicar</button>
            </div>
            <p id="cuponMsg" role="status" aria-live="polite" style="margin:8px 0 0; font-size:13px; font-weight:700;"></p>
          </div>
        </div>
      </div>

      <div class="panel" id="paymentPanel">
        <div class="panel-title"><h2>Método de pago</h2></div>
        <div class="panel-body">
          <form id="paymentForm" novalidate>
            <div class="payment-options" id="paymentOptions" role="radiogroup" aria-label="Método de pago">
              <label class="payment-option">
                <input type="radio" name="metodoPago" value="tarjeta" checked>
                Tarjeta de crédito o débito
              </label>
              <label class="payment-option">
                <input type="radio" name="metodoPago" value="transferencia">
                Transferencia bancaria
              </label>
              <label class="payment-option">
                <input type="radio" name="metodoPago" value="contraentrega">
                Pago contra entrega
              </label>
            </div>

            <div id="cardFields" style="margin-top:18px;">
              <div class="field">
                <label for="numeroTarjeta">Número de tarjeta</label>
                <input class="field-input" id="numeroTarjeta" name="numeroTarjeta" type="text" inputmode="numeric" maxlength="19" placeholder="0000 0000 0000 0000">
              </div>
              <div class="field" style="margin-top:18px;">
                <label for="nombreTarjeta">Nombre en la tarjeta</label>
                <input class="field-input" id="nombreTarjeta" name="nombreTarjeta" type="text" placeholder="Como aparece en la tarjeta">
              </div>
              <div class="form-grid form-grid--2" style="margin-top:18px;">
                <div class="field">
                  <label for="vencimiento">Vencimiento</label>
                  <input class="field-input" id="vencimiento" name="vencimiento" type="text" inputmode="numeric" maxlength="5" placeholder="MM/AA">
                </div>
                <div class="field">
                  <label for="cvv">CVV</label>
                  <input class="field-input" id="cvv" name="cvv" type="text" inputmode="numeric" maxlength="4" placeholder="123">
                </div>
              </div>
            </div>

            <div class="checkbox-row" style="margin-top:20px;">
              <input type="checkbox" id="aceptaTerminos" name="aceptaTerminos" required>
              <label for="aceptaTerminos" class="form-note">Acepto los términos y condiciones de compra.</label>
            </div>

            <button type="button" class="btn btn--accent btn--pill btn--block" id="confirmarBtn" style="margin-top:20px;">Confirmar y pagar</button>
            <p id="checkoutMsg" role="status" aria-live="polite" style="margin:12px 0 0; font-weight:800; display:none;"></p>
          </form>
        </div>
      </div>

    </div>

  </div>

  <div class="confirm-panel mt-lg" id="confirmPanel" hidden>
    <div class="confirm-panel__icon" aria-hidden="true">
      <svg width="34" height="34" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6 9 17l-5-5"/></svg>
    </div>
    <h2>¡Pedido confirmado!</h2>
    <p id="confirmMsg">Gracias por tu compra. Te enviaremos la confirmación a tu correo.</p>
    <a href="catalogo.php" class="btn btn--accent btn--pill">Seguir comprando</a>
  </div>

</main>

<footer class="site-footer">
  ChocoManía © <?php echo htmlspecialchars($anio); ?> · +56 9 1234 5678 · chocoatencion@chocomania.cl
</footer>

<script src="js/cart.js"></script>
<script src="js/api.js"></script>
<script src="js/common.js"></script>
<script src="js/carrito.js"></script>
</body>
</html>
