<?php
  $chocolates = [
    ["id" => 1, "nombre" => "Chocolate 70% cacao", "precio" => 3500],
    ["id" => 2, "nombre" => "Chocolate con avellanas", "precio" => 4200],
    ["id" => 3, "nombre" => "Chocolate blanco", "precio" => 3900],
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

    <script>
      const chocolates = <?php echo json_encode($chocolates); ?>;

      // Misma logica que index2.html del profe: al cargar la pagina,
      // se recorre el arreglo y se va llenando el combo.
      function cargarChocolates() {
        let cmb = document.getElementById("cmbChocolate");
        chocolates.forEach((choc) => {
          let opt = document.createElement("option");
          opt.setAttribute("value", choc.id);
          opt.innerText = choc.nombre + " - $" + choc.precio;
          cmb.appendChild(opt);
        });
      }

      // Misma logica que index.html del profe: boton que lee los inputs
      // y agrega una opcion nueva al combo, sin recargar la pagina.
      function agregarChocolate() {
        let cmb = document.getElementById("cmbChocolate");
        let nombre = document.getElementById("txtNombre").value;
        let precio = document.getElementById("txtPrecio").value;

        let opt = document.createElement("option");
        opt.setAttribute("value", nombre);
        opt.innerText = nombre + " - $" + precio;
        cmb.appendChild(opt);
      }
    </script>
  </head>

  <body onload="cargarChocolates();">

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

      <h4>Chocolates disponibles</h4>
      <select id="cmbChocolate" name="cmbChocolate"></select>

      <h4 class="mt-4">Agregar chocolate nuevo</h4>
      <input id="txtNombre" type="text" placeholder="Nombre"><br>
      <input id="txtPrecio" type="text" placeholder="Precio"><br>
      <button type="button" class="btn btn-outline-dark mt-2" onclick="agregarChocolate();">Agregar</button>

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