const { MongoClient, ObjectId } = require("mongodb");

// Cadena de conexion. Si tienes MongoDB corriendo localmente (mongod),
// esto deberia funcionar sin cambiar nada.
const URI = process.env.MONGO_URI || "mongodb://localhost:27017";
const DB_NAME = process.env.MONGO_DB || "chocomania";

const client = new MongoClient(URI);
let db = null;

async function conectarDB() {
  if (db) return db;
  await client.connect();
  db = client.db(DB_NAME);
  console.log(`Conectado a MongoDB -> base de datos "${DB_NAME}"`);
  return db;
}

module.exports = { conectarDB, ObjectId };
