<?php
  $productos = [
    ["id" => 1,  "nombre" => "Torta tres leches de chocolate",   "precio" => 15800, "descripcion" => "Bizcocho humedo banado en tres leches con cobertura de chocolate.", "imagen" => "https://images.unsplash.com/photo-1464349095431-e9a21285b5f3?q=80&w=500&auto=format&fit=crop"],
    ["id" => 2,  "nombre" => "Torta frutos del bosque",          "precio" => 16600, "descripcion" => "Bizcocho de vainilla, crema chantilly y frutos rojos frescos.",       "imagen" => "https://images.unsplash.com/photo-1578985545062-69928b1d9587?q=80&w=500&auto=format&fit=crop"],
    ["id" => 3,  "nombre" => "Torta de cumpleanos",               "precio" => 17900, "descripcion" => "Personalizable con mensaje y color a eleccion.",                    "imagen" => "https://images.unsplash.com/photo-1621303837174-89787a7d4729?q=80&w=500&auto=format&fit=crop"],
    ["id" => 4,  "nombre" => "Caja de cupcakes surtidos",         "precio" => 6500,  "descripcion" => "Chocolate, red velvet y limon. Caja de 3 unidades.",                "imagen" => "https://images.unsplash.com/photo-1517427294546-5aa121f68e8a?q=80&w=500&auto=format&fit=crop"],
    ["id" => 5,  "nombre" => "Brownie de chocolate 70%",          "precio" => 4200,  "descripcion" => "Chocolate 70% cacao con nueces tostadas.",                          "imagen" => "https://images.unsplash.com/photo-1550617931-e17a7b70dce2?q=80&w=500&auto=format&fit=crop"],
    ["id" => 6,  "nombre" => "Croissants de mantequilla",         "precio" => 5800,  "descripcion" => "Hojaldre 100% mantequilla, laminado a mano. Caja de 4.",            "imagen" => "https://images.unsplash.com/photo-1555507036-ab1f4038808a?q=80&w=500&auto=format&fit=crop"],
    ["id" => 7,  "nombre" => "Pie de limon individual",           "precio" => 3900,  "descripcion" => "Base crocante, crema de limon y merengue flameado.",                "imagen" => "https://images.unsplash.com/photo-1571115177098-24ec42ed204d?q=80&w=500&auto=format&fit=crop"],
    ["id" => 8,  "nombre" => "Pasteleria surtida",                "precio" => 8900,  "descripcion" => "Seleccion de pasteles individuales de la casa.",                    "imagen" => "https://images.unsplash.com/photo-1587668178277-295251f900ce?q=80&w=500&auto=format&fit=crop"],
    ["id" => 9,  "nombre" => "Panaderia dulce del dia",           "precio" => 5200,  "descripcion" => "Horneado fresco cada manana, mezcla del dia.",                      "imagen" => "https://images.unsplash.com/photo-1509440159596-0249088772ff?q=80&w=500&auto=format&fit=crop"],
    ["id" => 10, "nombre" => "Torta sin gluten de frutas",        "precio" => 18500, "descripcion" => "Elaborada en linea dedicada, decorada con frutas frescas.",          "imagen" => "https://images.unsplash.com/photo-1519869325930-281384150729?q=80&w=500&auto=format&fit=crop"],
    ["id" => 11, "nombre" => "Torta de chocolate a capas",        "precio" => 19900, "descripcion" => "Tres capas de bizcocho de chocolate con ganache.",                  "imagen" => "https://images.unsplash.com/photo-1464349095431-e9a21285b5f3?q=80&w=500&auto=format&fit=crop"],
    ["id" => 12, "nombre" => "Torta frambuesa y chocolate blanco","precio" => 17200, "descripcion" => "Bizcocho suave con crema de chocolate blanco y frambuesas.",        "imagen" => "https://images.unsplash.com/photo-1578985545062-69928b1d9587?q=80&w=500&auto=format&fit=crop"],
    ["id" => 13, "nombre" => "Torta especial de temporada",       "precio" => 21500, "descripcion" => "Receta rotativa segun la fruta de temporada.",                      "imagen" => "https://images.unsplash.com/photo-1621303837174-89787a7d4729?q=80&w=500&auto=format&fit=crop"],
    ["id" => 14, "nombre" => "Cupcakes de chocolate amargo",      "precio" => 6900,  "descripcion" => "Ganache de chocolate 70% sobre bizcocho de cacao.",                 "imagen" => "https://images.unsplash.com/photo-1517427294546-5aa121f68e8a?q=80&w=500&auto=format&fit=crop"],
    ["id" => 15, "nombre" => "Brownie con nueces y caramelo",     "precio" => 4500,  "descripcion" => "Nucleo de caramelo salado y nueces caramelizadas.",                 "imagen" => "https://images.unsplash.com/photo-1550617931-e17a7b70dce2?q=80&w=500&auto=format&fit=crop"],
    ["id" => 16, "nombre" => "Croissants rellenos de chocolate",  "precio" => 6200,  "descripcion" => "Relleno de chocolate semi amargo, caja de 4 unidades.",             "imagen" => "https://images.unsplash.com/photo-1555507036-ab1f4038808a?q=80&w=500&auto=format&fit=crop"],
    ["id" => 17, "nombre" => "Pie de chocolate y nuez",           "precio" => 4300,  "descripcion" => "Base de galleta, relleno de chocolate y nuez tostada.",             "imagen" => "https://images.unsplash.com/photo-1571115177098-24ec42ed204d?q=80&w=500&auto=format&fit=crop"],
    ["id" => 18, "nombre" => "Caja mixta de pasteleria",          "precio" => 9800,  "descripcion" => "Ocho piezas surtidas de la vitrina de la semana.",                  "imagen" => "https://images.unsplash.com/photo-1587668178277-295251f900ce?q=80&w=500&auto=format&fit=crop"],
  ];

  $buscarInicial = isset($_GET["buscar"]) ? $_GET["buscar"] : "";
?>
<!DOCTYPE html>
<html lang="es">
<head>
  <title>ChocoManía - Catálogo</title>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.8/dist/css/bootstrap.min.css" rel="stylesheet">
  <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.8/dist/js/bootstrap.bundle.min.js"></script>

  <style>
    :root{
      --cafe-oscuro:#582019;
      --banner:#ddd6be;
      --fondo-casillas:#ddc8c1;
      --botones:#804c3a;
      --texto:#ffffff;
    }

    body{
      background:var(--cafe-oscuro);
      color:var(--texto);
      font-family:'Segoe UI', Arial, sans-serif;
      margin:0;
    }

    .cm-header{
      background:var(--banner);
      display:flex;
      align-items:center;
      justify-content:space-between;
      padding:14px 30px;
    }
    .cm-logo{
      width:96px; height:96px; border-radius:50%;
      background:#ffffff; color:var(--cafe-oscuro);
      display:flex; align-items:center; justify-content:center;
      text-align:center; font-weight:700; font-size:15px; line-height:1.2;
      flex:0 0 auto;
    }
    .cm-nav{
      display:flex; gap:40px;
    }
    .cm-nav a{
      color:var(--cafe-oscuro); text-decoration:none;
      font-weight:700; font-size:22px;
    }
    .cm-nav a:hover{ opacity:.7; }
    .cm-search{
      display:flex; align-items:center; gap:8px;
      background:#ffffff; border-radius:999px; padding:6px 16px;
    }
    .cm-search input{
      border:0; outline:none; font-size:14px; min-width:160px;
    }

    .cm-shell{
      display:flex; align-items:flex-start; gap:24px;
      padding:24px 30px 40px;
    }
    .cm-col-cart{ width:250px; flex:0 0 auto; }
    .cm-col-catalog{ flex:1 1 auto; min-width:0; }
    .cm-col-offer{ width:300px; flex:0 0 auto; }

    .cart-box{
      background:var(--botones); border-radius:6px 6px 0 0; overflow:hidden;
    }
    .cart-box .cart-title{
      background:var(--botones); color:var(--texto);
      text-align:center; font-weight:700; font-size:22px; padding:10px 0;
    }
    .cart-box .cart-body{
      background:var(--fondo-casillas); color:var(--cafe-oscuro);
      min-height:320px; padding:18px; display:flex; flex-direction:column;
    }
    .cart-empty{
      flex:1; display:flex; flex-direction:column; align-items:center; justify-content:center;
      text-align:center; gap:14px;
    }
    .cart-empty p{ margin:0; font-weight:600; word-wrap:break-word; }
    .cart-items{ flex:1; }
    .cart-item{
      display:flex; justify-content:space-between; gap:8px;
      font-size:13px; padding:6px 0; border-bottom:1px solid rgba(88,32,25,.15);
      word-break:break-word;
    }
    .cart-total{
      font-weight:700; text-align:right; margin-top:10px; padding-top:8px;
      border-top:2px solid var(--cafe-oscuro); font-size:14px;
    }
    .btn-pagar{
      display:block; width:100%; border:0; padding:14px 0;
      background:var(--botones); color:var(--texto);
      font-weight:700; font-size:18px; letter-spacing:.05em;
      border-radius:0 0 6px 6px;
    }

    .product-grid{
      display:grid; grid-template-columns:repeat(3, 1fr); gap:16px;
    }
    .product-card{
      background:#ffffff; color:var(--cafe-oscuro); border-radius:4px; overflow:hidden;
      display:flex; flex-direction:column;
    }
    .product-card .thumb{ height:130px; overflow:hidden; }
    .product-card .thumb img{ width:100%; height:100%; object-fit:cover; }
    .product-card .info{ padding:10px 12px; flex:1; display:flex; flex-direction:column; }
    .product-card .info h5{ font-size:14px; font-weight:700; margin:0 0 4px; }
    .product-card .info p{ font-size:11.5px; color:#6b4f49; flex:1; margin:0 0 8px; }
    .product-card .row-buy{
      display:flex; align-items:center; justify-content:space-between;
    }
    .product-card .price{ font-weight:700; color:var(--cafe-oscuro); font-size:14px; }
    .btn-buy{
      border:0; background:var(--botones); color:var(--texto);
      font-size:11px; font-weight:700; letter-spacing:.05em;
      padding:6px 14px; border-radius:2px 10px 10px 2px;
    }

    .cm-pagination{
      display:flex; align-items:center; justify-content:center; gap:20px;
      margin-top:20px;
    }
    .page-arrow{
      width:36px; height:36px; border-radius:50%; border:0;
      background:#ffffff; color:var(--cafe-oscuro); font-size:18px; font-weight:700;
    }
    .page-number{ font-size:20px; }

    .offer-title{ font-weight:700; font-size:22px; margin-bottom:10px; }
    .offer-name{
      background:var(--fondo-casillas); color:var(--cafe-oscuro);
      font-weight:700; text-align:center; padding:10px; border-radius:4px; margin-bottom:14px;
    }
    .offer-panel{
      background:var(--fondo-casillas); border-radius:6px; padding:24px 18px; text-align:center;
    }
    .offer-panel .offer-photo{
      width:200px; height:200px; border-radius:50%; overflow:hidden;
      margin:0 auto 18px; background:#ffffff;
    }
    .offer-panel .offer-photo img{ width:100%; height:100%; object-fit:cover; }
    .offer-prices{ margin-bottom:16px; }
    .offer-prices .old-price{ text-decoration:line-through; color:#6b4f49; font-size:14px; margin-right:10px; }
    .offer-prices .sale-price{ color:var(--cafe-oscuro); font-weight:700; font-size:18px; }
    .offer-buttons{ display:flex; gap:10px; justify-content:center; }
    .btn-offer{
      border:0; background:var(--botones); color:var(--texto);
      font-size:13px; font-weight:600; padding:8px 14px; border-radius:4px;
    }
  </style>
</head>
<body>

  <header class="cm-header">
    <div class="cm-logo"><a href="index.php" style="color:inherit; text-decoration:none;">Choco<br>Manía</a></div>
    <nav class="cm-nav">
      <a href="empresa.php">Sobre Nosotros</a>
      <a href="productos.php">Catálogo</a>
      <a href="servicios.php">Servicios</a>
    </nav>
    <div class="cm-search">
      <span>&#128269;</span>
      <input type="text" id="txtBuscar" placeholder="Buscar producto..." value="<?php echo htmlspecialchars($buscarInicial); ?>" oninput="onBuscar(this.value)">
    </div>
  </header>

  <div class="cm-shell">

    <div class="cm-col-cart">
      <div class="cart-box">
        <div class="cart-title">Carrito</div>
        <div class="cart-body">
          <div id="cartEmpty" class="cart-empty">
            <p>Aún no eliges nada!!</p>
            <div style="font-size:40px;">&#128722;</div>
            <p>No pierdas la oportunidad de darte un gusto!</p>
          </div>
          <div id="cartItems" class="cart-items" style="display:none;"></div>
          <div id="cartTotal" class="cart-total" style="display:none;"></div>
        </div>
        <button type="button" class="btn-pagar">PAGAR</button>
      </div>
    </div>

    <div class="cm-col-catalog">
      <div id="productGrid" class="product-grid"></div>
      <div class="cm-pagination">
        <button type="button" class="page-arrow" onclick="paginaAnterior();">&#8249;</button>
        <span id="pageNumber" class="page-number">1</span>
        <button type="button" class="page-arrow" onclick="paginaSiguiente();">&#8250;</button>
      </div>
    </div>

    <div class="cm-col-offer">
      <div class="offer-title">OFERTAS</div>
      <div id="offerName" class="offer-name"></div>
      <div class="offer-panel">
        <div class="offer-photo"><img id="offerImg" src="" alt=""></div>
        <div class="offer-prices">
          <span id="offerOldPrice" class="old-price"></span>
          <span id="offerSalePrice" class="sale-price"></span>
        </div>
        <div class="offer-buttons">
          <button type="button" class="btn-offer">Detalles</button>
          <button type="button" class="btn-offer">&#128722;+ Agregar</button>
        </div>
      </div>
    </div>

  </div>

  <script>

    const productos = <?php echo json_encode($productos); ?>;

    const PAGE_SIZE = 9;
    let paginaActual = 1;
    let textoBusqueda = <?php echo json_encode($buscarInicial); ?>;
    let carrito = []; // cada item: { id, nombre, precio, cantidad }

    function formatearPrecio(numero) {
      return "$" + numero.toLocaleString("es-CL");
    }

    function obtenerProductosFiltrados() {
      if (textoBusqueda.trim() === "") {
        return productos;
      }
      return productos.filter((p) =>
        p.nombre.toLowerCase().includes(textoBusqueda.toLowerCase())
      );
    }

    function renderizarGrid() {
      let filtrados = obtenerProductosFiltrados();
      let totalPaginas = Math.max(1, Math.ceil(filtrados.length / PAGE_SIZE));
      if (paginaActual > totalPaginas) paginaActual = totalPaginas;
      if (paginaActual < 1) paginaActual = 1;

      let inicio = (paginaActual - 1) * PAGE_SIZE;
      let productosPagina = filtrados.slice(inicio, inicio + PAGE_SIZE);

      let grid = document.getElementById("productGrid");
      grid.innerHTML = "";

      if (productosPagina.length === 0) {
        grid.innerHTML = "<p style='color:#ffffff; grid-column: 1 / -1; text-align:center;'>No se encontraron productos.</p>";
      }

      productosPagina.forEach((p) => {
        let card = document.createElement("div");
        card.className = "product-card";
        card.innerHTML =
          '<div class="thumb"><img src="' + p.imagen + '" alt="' + p.nombre + '"></div>' +
          '<div class="info">' +
            '<h5>' + p.nombre + '</h5>' +
            '<p>' + p.descripcion + '</p>' +
            '<div class="row-buy">' +
              '<span class="price">' + formatearPrecio(p.precio) + '</span>' +
              '<button type="button" class="btn-buy" onclick="agregarAlCarrito(' + p.id + ');">BUY</button>' +
            '</div>' +
          '</div>';
        grid.appendChild(card);
      });

      document.getElementById("pageNumber").innerText = paginaActual;
    }

    function paginaSiguiente() {
      let filtrados = obtenerProductosFiltrados();
      let totalPaginas = Math.max(1, Math.ceil(filtrados.length / PAGE_SIZE));
      if (paginaActual < totalPaginas) {
        paginaActual++;
        renderizarGrid();
      }
    }

    function paginaAnterior() {
      if (paginaActual > 1) {
        paginaActual--;
        renderizarGrid();
      }
    }

    function onBuscar(valor) {
      textoBusqueda = valor;
      paginaActual = 1;
      renderizarGrid();
    }

    function agregarAlCarrito(id) {
      let producto = productos.find((p) => p.id === id);
      let existente = carrito.find((item) => item.id === id);
      if (existente) {
        existente.cantidad++;
      } else {
        carrito.push({ id: producto.id, nombre: producto.nombre, precio: producto.precio, cantidad: 1 });
      }
      renderizarCarrito();
    }

    function renderizarCarrito() {
      let cartEmpty = document.getElementById("cartEmpty");
      let cartItemsDiv = document.getElementById("cartItems");
      let cartTotalDiv = document.getElementById("cartTotal");

      if (carrito.length === 0) {
        cartEmpty.style.display = "flex";
        cartItemsDiv.style.display = "none";
        cartTotalDiv.style.display = "none";
        return;
      }

      cartEmpty.style.display = "none";
      cartItemsDiv.style.display = "block";
      cartTotalDiv.style.display = "block";

      cartItemsDiv.innerHTML = "";
      let total = 0;
      carrito.forEach((item) => {
        total += item.precio * item.cantidad;
        let fila = document.createElement("div");
        fila.className = "cart-item";
        fila.innerHTML =
          "<span>" + item.nombre + " x" + item.cantidad + "</span>" +
          "<span>" + formatearPrecio(item.precio * item.cantidad) + "</span>";
        cartItemsDiv.appendChild(fila);
      });

      cartTotalDiv.innerText = "Total: " + formatearPrecio(total);
    }

    function cargarOfertaAleatoria() {
      let indice = Math.floor(Math.random() * productos.length);
      let producto = productos[indice];
      let precioOferta = Math.round(producto.precio * 0.8); // 20% de descuento

      document.getElementById("offerName").innerText = producto.nombre;
      document.getElementById("offerImg").src = producto.imagen;
      document.getElementById("offerImg").alt = producto.nombre;
      document.getElementById("offerOldPrice").innerText = formatearPrecio(producto.precio);
      document.getElementById("offerSalePrice").innerText = formatearPrecio(precioOferta);
    }

    renderizarGrid();
    renderizarCarrito();
    cargarOfertaAleatoria();
  </script>

</body>
</html>
