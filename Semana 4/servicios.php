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

    <nav class="navbar navbar-expand-sm bg-dark navbar-dark">
      <div class="container-fluid">
        <a class="navbar-brand" href="index.php">ChocoManía</a>
        <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#collapsibleNavbar">
          <span class="navbar-toggler-icon"></span>
        </button>
        <div class="collapse navbar-collapse" id="collapsibleNavbar">
          <ul class="navbar-nav">
            <li class="nav-item dropdown">
              <a class="nav-link dropdown-toggle" href="#" role="button" data-bs-toggle="dropdown">Empresa</a>
              <ul class="dropdown-menu">
                <li><a class="dropdown-item" href="empresa.php">Quienes Somos</a></li>
                <li><a class="dropdown-item" href="#">Nuestro Equipo</a></li>
                <li><a class="dropdown-item" href="#">Mision</a></li>
              </ul>
            </li>
            <li class="nav-item">
              <a class="nav-link" href="productos.php">Productos</a>
            </li>
            <li class="nav-item">
              <a class="nav-link" href="servicios.php">Servicios</a>
            </li>
            <li class="nav-item">
              <a class="nav-link" href="contacto.php">Contacto</a>
            </li>
          </ul>
        </div>
      </div>
    </nav>

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