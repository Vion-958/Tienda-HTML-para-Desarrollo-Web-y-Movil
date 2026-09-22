<?php
// Catálogo de respaldo, compartido por catalogo.php y producto.php.
// Los primeros 5 son los mismos productos que seed.js carga en MongoDB
// para el backend GraphQL (../chocomania-graphql/seed.js); el resto son
// productos de prueba agregados para tener más categorías y probar el
// filtrado/paginación del catálogo. Cuando el backend GraphQL no está
// disponible, js/api.js usa este arreglo para que el sitio siga siendo
// completamente navegable. Cada producto trae su "categoria" ya
// asignada (js/api.js la respeta si viene definida; solo la infiere
// por texto cuando falta, como pasaría con datos que sí vinieran del
// backend GraphQL, que no expone ese campo).
return [
  [
    "id" => "demo-1",
    "nombre" => "Torta tres leches de chocolate",
    "precio" => 15800,
    "descripcion" => "Bizcocho húmedo bañado en tres leches con cobertura de chocolate.",
    "imagen" => "https://images.unsplash.com/photo-1464349095431-e9a21285b5f3?q=80&w=500&auto=format&fit=crop",
    "categoria" => "De leche",
  ],
  [
    "id" => "demo-2",
    "nombre" => "Torta frutos del bosque",
    "precio" => 16600,
    "descripcion" => "Bizcocho de vainilla, crema chantilly y frutos rojos frescos.",
    "imagen" => "https://images.unsplash.com/photo-1578985545062-69928b1d9587?q=80&w=500&auto=format&fit=crop",
    "categoria" => "De leche",
  ],
  [
    "id" => "demo-3",
    "nombre" => "Torta de cumpleaños",
    "precio" => 17900,
    "descripcion" => "Personalizable con mensaje y color a elección.",
    "imagen" => "https://images.unsplash.com/photo-1621303837174-89787a7d4729?q=80&w=500&auto=format&fit=crop",
    "categoria" => "De leche",
  ],
  [
    "id" => "demo-4",
    "nombre" => "Caja de cupcakes surtidos",
    "precio" => 6500,
    "descripcion" => "Chocolate, red velvet y limón. Caja de 3 unidades.",
    "imagen" => "https://images.unsplash.com/photo-1517427294546-5aa121f68e8a?q=80&w=500&auto=format&fit=crop",
    "categoria" => "Postres",
  ],
  [
    "id" => "demo-5",
    "nombre" => "Brownie de chocolate 70%",
    "precio" => 4200,
    "descripcion" => "Chocolate 70% cacao con nueces tostadas.",
    "imagen" => "https://images.unsplash.com/photo-1550617931-e17a7b70dce2?q=80&w=500&auto=format&fit=crop",
    "categoria" => "Amargo",
  ],
  [
    "id" => "demo-6",
    "nombre" => "Torta red velvet",
    "precio" => 18500,
    "descripcion" => "Bizcocho aterciopelado con relleno de queso crema y toque de cacao.",
    "imagen" => "https://images.unsplash.com/photo-1621303837174-89787a7d4729?q=80&w=500&auto=format&fit=crop",
    "categoria" => "De leche",
  ],
  [
    "id" => "demo-7",
    "nombre" => "Alfajores bañados en chocolate",
    "precio" => 5200,
    "descripcion" => "Alfajores artesanales rellenos de manjar, bañados en chocolate con leche.",
    "imagen" => "https://images.unsplash.com/photo-1517427294546-5aa121f68e8a?q=80&w=500&auto=format&fit=crop",
    "categoria" => "De leche",
  ],
  [
    "id" => "demo-8",
    "nombre" => "Barra chocolate amargo 85%",
    "precio" => 4800,
    "descripcion" => "Chocolate 85% cacao de origen único, intenso y sin relleno.",
    "imagen" => "https://images.unsplash.com/photo-1550617931-e17a7b70dce2?q=80&w=500&auto=format&fit=crop",
    "categoria" => "Amargo",
  ],
  [
    "id" => "demo-9",
    "nombre" => "Trufas de chocolate amargo",
    "precio" => 6900,
    "descripcion" => "Trufas artesanales con ganache 70% cacao y cobertura amarga.",
    "imagen" => "img/servicio-cocteles.jpg",
    "categoria" => "Amargo",
  ],
  [
    "id" => "demo-10",
    "nombre" => "Torta vegana de chocolate",
    "precio" => 19900,
    "descripcion" => "Bizcocho 100% plant-based con ganache vegano, sin huevo ni lácteos.",
    "imagen" => "https://images.unsplash.com/photo-1464349095431-e9a21285b5f3?q=80&w=500&auto=format&fit=crop",
    "categoria" => "Vegana",
  ],
  [
    "id" => "demo-11",
    "nombre" => "Brownie vegano sin gluten",
    "precio" => 4700,
    "descripcion" => "Brownie húmedo con harina de almendras, sin gluten, huevo ni lácteos.",
    "imagen" => "https://images.unsplash.com/photo-1550617931-e17a7b70dce2?q=80&w=500&auto=format&fit=crop",
    "categoria" => "Vegana",
  ],
  [
    "id" => "demo-12",
    "nombre" => "Chocolate sin azúcar con stevia",
    "precio" => 5500,
    "descripcion" => "Barra de chocolate endulzada con stevia, ideal para un consumo más consciente.",
    "imagen" => "https://images.unsplash.com/photo-1550617931-e17a7b70dce2?q=80&w=500&auto=format&fit=crop",
    "categoria" => "Sin azúcar",
  ],
  [
    "id" => "demo-13",
    "nombre" => "Bombones sin azúcar surtidos",
    "precio" => 7200,
    "descripcion" => "Caja de bombones rellenos endulzados con maltitol, sin azúcar añadida.",
    "imagen" => "img/servicio-cocteles.jpg",
    "categoria" => "Sin azúcar",
  ],
  [
    "id" => "demo-14",
    "nombre" => "Caja por mayor 50 chocolates",
    "precio" => 45000,
    "descripcion" => "Caja al por mayor con 50 chocolates surtidos, ideal para eventos y revendedores.",
    "imagen" => "img/servicio-regalos.png",
    "categoria" => "Por mayor",
  ],
  [
    "id" => "demo-15",
    "nombre" => "Pack por mayor 100 mini brownies",
    "precio" => 62000,
    "descripcion" => "Pack al por mayor de 100 mini brownies individuales, precio especial por volumen.",
    "imagen" => "img/servicio-regalos.png",
    "categoria" => "Por mayor",
  ],
];
