<?php
  $servicios = [
    ["id" => 1, "nombre" => "Cajas de chocolate personalizadas", "precio" => 12000],
    ["id" => 2, "nombre" => "Taller de chocolatería", "precio" => 15000],
    ["id" => 3, "nombre" => "Catering de eventos", "precio" => 45000],
  ];
?>
<!DOCTYPE html>
<html lang="es">
  <head>
    <title>ChocoManía - Servicios</title>
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
      const servicios = <?php echo json_encode($servicios); ?>;

      function cargarServicios() {
        let cmb = document.getElementById("cmbServicio");
        servicios.forEach((serv) => {
          let opt = document.createElement("option");
          opt.setAttribute("value", serv.id);
          opt.innerText = serv.nombre + " - $" + serv.precio;
          cmb.appendChild(opt);
        });
      }

      function agregarServicio() {
        let cmb = document.getElementById("cmbServicio");
        let nombre = document.getElementById("txtNombre").value;
        let precio = document.getElementById("txtPrecio").value;

        let opt = document.createElement("option");
        opt.setAttribute("value", nombre);
        opt.innerText = nombre + " - $" + precio;
        cmb.appendChild(opt);
      }
    </script>
  </head>

  <body onload="cargarServicios();">

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

      <h4>Servicios disponibles</h4>
      <select id="cmbServicio" name="cmbServicio"></select>

      <h4 class="mt-4">Agregar servicio nuevo</h4>
      <input id="txtNombre" type="text" placeholder="Nombre"><br>
      <input id="txtPrecio" type="text" placeholder="Precio"><br>
      <button type="button" class="btn btn-outline-dark mt-2" onclick="agregarServicio();">Agregar</button>

    </div>

    <div class="container-fluid bg-dark text-light text-center p-3">
      <div class="row">
        <div class="col-4" style="color: white;"><strong>ChocoManía@2026</strong></div>
        <div class="col-4"></div>
        <div class="col-4"></div>
      </div>
    </div>

  </body>
</html>
