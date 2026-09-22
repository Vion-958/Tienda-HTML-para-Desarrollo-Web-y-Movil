// Levanta un MongoDB en memoria (mongodb-memory-server), carga los mismos
// productos de seed.js (con imagenes free-use de Unsplash) y despues arranca
// el servidor GraphQL real del proyecto (server.js) apuntando a esa base temporal.
// Solo para pruebas locales: no modifica ni reemplaza el flujo normal con
// un mongod persistente descrito en el README del backend.
const path = "C:/Users/Vicente/Downloads/chocomania-graphql(1)/chocomania-graphql";
process.chdir(path);

const { MongoMemoryServer } = require("mongodb-memory-server");

const productos = [
  { nombre: "Torta tres leches de chocolate", precio: 15800, descripcion: "Bizcocho humedo banado en tres leches con cobertura de chocolate.", imagen: "https://images.unsplash.com/photo-1464349095431-e9a21285b5f3?q=80&w=500&auto=format&fit=crop" },
  { nombre: "Torta frutos del bosque", precio: 16600, descripcion: "Bizcocho de vainilla, crema chantilly y frutos rojos frescos.", imagen: "https://images.unsplash.com/photo-1578985545062-69928b1d9587?q=80&w=500&auto=format&fit=crop" },
  { nombre: "Torta de cumpleanos", precio: 17900, descripcion: "Personalizable con mensaje y color a eleccion.", imagen: "https://images.unsplash.com/photo-1621303837174-89787a7d4729?q=80&w=500&auto=format&fit=crop" },
  { nombre: "Caja de cupcakes surtidos", precio: 6500, descripcion: "Chocolate, red velvet y limon. Caja de 3 unidades.", imagen: "https://images.unsplash.com/photo-1517427294546-5aa121f68e8a?q=80&w=500&auto=format&fit=crop" },
  { nombre: "Brownie de chocolate 70%", precio: 4200, descripcion: "Chocolate 70% cacao con nueces tostadas.", imagen: "https://images.unsplash.com/photo-1550617931-e17a7b70dce2?q=80&w=500&auto=format&fit=crop" },
];

async function main() {
  const mongod = await MongoMemoryServer.create({ instance: { dbName: "chocomania" } });
  const uri = mongod.getUri();
  process.env.MONGO_URI = uri;
  process.env.MONGO_DB = "chocomania";
  console.log("MONGO_MEMORY_URI=" + uri);

  const { conectarDB } = require(path + "/db.js");
  const db = await conectarDB();
  await db.collection("productos").insertMany(productos);
  console.log(`Seed: ${productos.length} productos insertados en la base temporal.`);

  require(path + "/server.js");
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
