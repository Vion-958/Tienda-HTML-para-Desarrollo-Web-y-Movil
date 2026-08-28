<?php
  $motivos = [
    ["id" => 1, "nombre" => "Consulta por pedido"],
    ["id" => 2, "nombre" => "Reclamo"],
    ["id" => 3, "nombre" => "Trabajemos juntos"],
  ];
?>
<!DOCTYPE html>
<html lang="es">
  <head>
    <title>ChocoManía - Contacto</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.8/dist/css/bootstrap.min.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.8/dist/js/bootstrap.bundle.min.js"></script>

    <script>
      const motivos = <?php echo json_encode($motivos); ?>;

      function cargarMotivos() {
        let cmb = document.getElementById("cmbMotivo");
        motivos.forEach((mot) => {
          let opt = document.createElement("option");
          opt.setAttribute("value", mot.id);
          opt.innerText = mot.nombre;
          cmb.appendChild(opt);
        });
      }

      function agregarMotivo() {
        let cmb = document.getElementById("cmbMotivo");
        let nombre = document.getElementById("txtMotivo").value;

        let opt = document.createElement("option");
        opt.setAttribute("value", nombre);
        opt.innerText = nombre;
        cmb.appendChild(opt);
      }
    </script>
  </head>

  <body onload="cargarMotivos();">

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

      <form action="empresa.php">
        <div class="mb-2 mt-2">
          <label for="email" class="form-label">Email:</label>
          <input type="email" class="form-control" id="email" placeholder="Enter email" name="email">
        </div>
        <label for="comment">Comentarios</label>
        <textarea class="form-control" rows="5" id="comment" name="text"></textarea>
        <button type="button" class="btn btn-outline-primary mt-1">Enviar</button>
        <a href="index.php">Volver</a>
      </form>

      <h4 class="mt-4">Motivo de contacto</h4>
      <select id="cmbMotivo" name="cmbMotivo"></select>

      <h4 class="mt-4">Agregar motivo nuevo</h4>
      <input id="txtMotivo" type="text" placeholder="Motivo"><br>
      <button type="button" class="btn btn-outline-dark mt-2" onclick="agregarMotivo();">Agregar</button>

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