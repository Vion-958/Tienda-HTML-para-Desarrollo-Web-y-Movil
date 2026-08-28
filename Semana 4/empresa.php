<?php
  $equipo = [
    ["id" => 1, "nombre" => "María José - Chocolatera jefe"],
    ["id" => 2, "nombre" => "Tomás - Maestro chocolatero"],
    ["id" => 3, "nombre" => "Constanza - Atención a clientes"],
  ];
?>
<!DOCTYPE html>
<html lang="es">
  <head>
    <title>ChocoManía - Empresa</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.8/dist/css/bootstrap.min.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.8/dist/js/bootstrap.bundle.min.js"></script>

    <script>
      const equipo = <?php echo json_encode($equipo); ?>;

      function cargarEquipo() {
        let cmb = document.getElementById("cmbEquipo");
        equipo.forEach((integrante) => {
          let opt = document.createElement("option");
          opt.setAttribute("value", integrante.id);
          opt.innerText = integrante.nombre;
          cmb.appendChild(opt);
        });
      }

      function agregarIntegrante() {
        let cmb = document.getElementById("cmbEquipo");
        let nombre = document.getElementById("txtIntegrante").value;

        let opt = document.createElement("option");
        opt.setAttribute("value", nombre);
        opt.innerText = nombre;
        cmb.appendChild(opt);
      }
    </script>
  </head>

  <body onload="cargarEquipo();">

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

      <h4>Quiénes somos</h4>
      <p>ChocoManía es una chocolatería artesanal dedicada a crear chocolates de autor, hechos a mano en pequeños lotes.</p>

      <h4 class="mt-4">Nuestro equipo</h4>
      <select id="cmbEquipo" name="cmbEquipo"></select>

      <h4 class="mt-4">Agregar integrante</h4>
      <input id="txtIntegrante" type="text" placeholder="Nombre - Cargo"><br>
      <button type="button" class="btn btn-outline-dark mt-2" onclick="agregarIntegrante();">Agregar</button><br>

      <a href="index.php" class="d-inline-block mt-3">Volver</a>
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