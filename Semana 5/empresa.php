<?php
  $equipo = [
    ["id" => 1, "nombre" => "María José - Chocolatera jefe"],
    ["id" => 2, "nombre" => "Tomás - Maestro chocolatero"],
    ["id" => 3, "nombre" => "Constanza - Atención a clientes"],
  ];

  $motivos = [
    ["id" => 1, "nombre" => "Consulta por pedido"],
    ["id" => 2, "nombre" => "Reclamo"],
    ["id" => 3, "nombre" => "Trabajemos juntos"],
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
      const equipo = <?php echo json_encode($equipo); ?>;

      // Igual que en las otras paginas: al cargar la pagina, se llena el combo.
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

  <body onload="cargarEquipo(); cargarMotivos();">

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

      <h4>Quiénes somos</h4>
      <p>ChocoManía es una chocolatería artesanal dedicada a crear chocolates de autor, hechos a mano en pequeños lotes.</p>

      <h4 class="mt-4">Nuestro equipo</h4>
      <select id="cmbEquipo" name="cmbEquipo"></select>

      <h4 class="mt-4">Agregar integrante</h4>
      <input id="txtIntegrante" type="text" placeholder="Nombre - Cargo"><br>
      <button type="button" class="btn btn-outline-dark mt-2" onclick="agregarIntegrante();">Agregar</button><br>

      <hr class="mt-4">

      <h4 class="mt-4">Contacto</h4>
      <form action="empresa.php">
        <div class="mb-2 mt-2">
          <label for="email" class="form-label">Email:</label>
          <input type="email" class="form-control" id="email" placeholder="Enter email" name="email">
        </div>
        <label for="comment">Comentarios</label>
        <textarea class="form-control" rows="5" id="comment" name="text"></textarea>
        <button type="button" class="btn btn-outline-primary mt-1">Enviar</button>
      </form>

      <h4 class="mt-4">Motivo de contacto</h4>
      <select id="cmbMotivo" name="cmbMotivo"></select>

      <h4 class="mt-4">Agregar motivo nuevo</h4>
      <input id="txtMotivo" type="text" placeholder="Motivo"><br>
      <button type="button" class="btn btn-outline-dark mt-2" onclick="agregarMotivo();">Agregar</button>

      <br>
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
