const { conectarDB } = require("./db");

const productos = [
  { nombre: "Torta tres leches de chocolate", precio: 15800, descripcion: "Bizcocho humedo banado en tres leches con cobertura de chocolate.", imagen: "https://images.unsplash.com/photo-1464349095431-e9a21285b5f3?q=80&w=500&auto=format&fit=crop" },
  { nombre: "Torta frutos del bosque", precio: 16600, descripcion: "Bizcocho de vainilla, crema chantilly y frutos rojos frescos.", imagen: "https://images.unsplash.com/photo-1578985545062-69928b1d9587?q=80&w=500&auto=format&fit=crop" },
  { nombre: "Torta de cumpleanos", precio: 17900, descripcion: "Personalizable con mensaje y color a eleccion.", imagen: "https://images.unsplash.com/photo-1621303837174-89787a7d4729?q=80&w=500&auto=format&fit=crop" },
  { nombre: "Caja de cupcakes surtidos", precio: 6500, descripcion: "Chocolate, red velvet y limon. Caja de 3 unidades.", imagen: "https://images.unsplash.com/photo-1517427294546-5aa121f68e8a?q=80&w=500&auto=format&fit=crop" },
  { nombre: "Brownie de chocolate 70%", precio: 4200, descripcion: "Chocolate 70% cacao con nueces tostadas.", imagen: "https://images.unsplash.com/photo-1550617931-e17a7b70dce2?q=80&w=500&auto=format&fit=crop" },
];

async function seed() {
  const db = await conectarDB();
  const coleccion = db.collection("productos");

  await coleccion.deleteMany({});
  const resultado = await coleccion.insertMany(productos);

  console.log(`Se insertaron ${resultado.insertedCount} productos en MongoDB.`);
  process.exit(0);
}

seed().catch((err) => {
  console.error("Error al cargar los datos:", err);
  process.exit(1);
});
