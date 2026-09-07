<?php
  $destacados = [
    ["id" => 1, "nombre" => "Chocolate 70% cacao - Destacado de agosto"],
  ];
?>
<!DOCTYPE html>
<html lang="es">
  <head>
    <title>ChocoManía</title>
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
      .cm-header{
        background:var(--banner);
        display:flex; align-items:center; justify-content:space-between;
        padding:14px 30px;
      }
      .cm-logo{
        width:96px; height:96px; border-radius:50%;
        background:#ffffff; color:var(--cafe-oscuro);
        display:flex; align-items:center; justify-content:center;
        text-align:center; font-weight:700; font-size:15px; line-height:1.2;
        flex:0 0 auto; text-decoration:none;
      }
      .cm-nav{ display:flex; gap:40px; }
      .cm-nav a{ color:var(--cafe-oscuro); text-decoration:none; font-weight:700; font-size:22px; }
      .cm-nav a:hover{ opacity:.7; }
      .cm-search{ display:flex; align-items:center; gap:8px; background:#ffffff; border-radius:999px; padding:6px 16px; }
      .cm-search input{ border:0; outline:none; font-size:14px; min-width:160px; }
    </style>

    <script>
      const destacados = <?php echo json_encode($destacados); ?>;

      function cargarDestacados() {
        let cmb = document.getElementById("cmbDestacado");
        destacados.forEach((dest) => {
          let opt = document.createElement("option");
          opt.setAttribute("value", dest.id);
          opt.innerText = dest.nombre;
          cmb.appendChild(opt);
        });
      }

      function agregarDestacado() {
        let cmb = document.getElementById("cmbDestacado");
        let nombre = document.getElementById("txtDestacado").value;

        let opt = document.createElement("option");
        opt.setAttribute("value", nombre);
        opt.innerText = nombre;
        cmb.appendChild(opt);
      }
    </script>
  </head>

  <body onload="cargarDestacados();">

    <header class="cm-header">
      <a href="index.php" class="cm-logo">Choco<br>Manía</a>
      <nav class="cm-nav">
        <a href="empresa.php">Sobre Nosotros</a>
        <a href="productos.php">Catálogo</a>
        <a href="servicios.php">Servicios</a>
      </nav>
      <div class="cm-search">
        <span>&#128269;</span>
        <input type="text" placeholder="Buscar producto..."
          onkeypress="if(event.key==='Enter'){window.location.href='productos.php?buscar='+encodeURIComponent(this.value);}">
      </div>
    </header>

    <div class="container-fluid bg-warning p-3">
      <button type="button" class="btn btn-outline-dark mb-3" data-bs-toggle="modal" data-bs-target="#myModal">Acceder</button><br>
      <a href="empresa.php">Ir a Empresa</a><br>
      <a href="productos.php">Ir a Productos</a><br>
      <a href="servicios.php">Ir a Servicios</a><br>

      <h4 class="mt-4">Chocolate destacado del mes</h4>
      <select id="cmbDestacado" name="cmbDestacado"></select>

      <h4 class="mt-4">Agregar destacado</h4>
      <input id="txtDestacado" type="text" placeholder="Nombre del destacado"><br>
      <button type="button" class="btn btn-outline-dark mt-2" onclick="agregarDestacado();">Agregar</button>
    </div>

    <div class="container-fluid bg-dark text-light text-center p-3">
      <div class="row">
        <div class="col-4" style="color: white;"><strong>ChocoManía@2026</strong></div>
        <div class="col-4"></div>
        <div class="col-4"></div>
      </div>
    </div>

    <div class="modal fade" id="myModal">
      <div class="modal-dialog">
        <div class="modal-content">
          <div class="modal-header">
            <h4 class="modal-title">Autenticación</h4>
            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
          </div>
          <div class="modal-body">
            <form action="empresa.php">
              <div class="mb-3 mt-3">
                <label for="email" class="form-label">Email:</label>
                <input type="email" class="form-control" id="email" placeholder="Enter email" name="email">
              </div>
              <div class="mb-3">
                <label for="pwd" class="form-label">Password:</label>
                <input type="password" class="form-control" id="pwd" placeholder="Enter password" name="pswd">
              </div>
              <div class="form-check mb-3">
                <label class="form-check-label">
                  <input class="form-check-input" type="checkbox" name="remember"> Remember me
                </label>
              </div>
              <button type="submit" class="btn btn-primary">Login</button>
            </form>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-danger" data-bs-dismiss="modal">Close</button>
          </div>
        </div>
      </div>
    </div>

  </body>
</html>
