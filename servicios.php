<!DOCTYPE html>
<html lang="es">
  <html>
      <head>
          <title>Mi Pagina Web</title>
          <meta charset="utf-8">
          <meta name="viewport" content="width=device-width, initial-scale=1">
          <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.8/dist/css/bootstrap.min.css" rel="stylesheet">
          <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.8/dist/js/bootstrap.bundle.min.js"></script>
    </head>
    <body>
      <!-- Navbar -->
      <nav class="navbar navbar-expand-sm bg-dark navbar-dark">
      <div class="container-fluid">
        <a class="navbar-brand" href="index.php">Logo</a>
        <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#collapsibleNavbar">
        <span class="navbar-toggler-icon"></span>
        </button>
        <div class="collapse navbar-collapse" id="collapsibleNavbar">
              <ul class="navbar-nav">
                <li class="nav-item dropdown">
                  <a class="nav-link dropdown-toggle" href="#" role="button" data-bs-toggle="dropdown">Empresa</a>
                  <ul class="dropdown-menu">
                    <li><a class="dropdown-item" href="#">Quienes Somos</a></li>
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
      <!-- Container -->
         <div class="container-fluid bg-warning">
            
        <a href="empresa.php">Ir a Empresa</a><br>
        <a href="productos.php">Ir a Productos</a><br>
        <a href="servicios.php">Ir a Servicios</a><br>
        <a href="contacto.php">Ir a Contacto</a><br>
      </div>
      <!-- Footer -->
       <div class="container-fluid bg-dark text-light text-center p-3">
        <div class="row">
          <div class="col-4" style="color: white;"><strong>MiEmpresa@2026</strong></div>
          <div class="col-4"></div>
          <div class="col-4"></div>
        </div>
      </div>
      <!-- Modal -->
    </body>
  </html>