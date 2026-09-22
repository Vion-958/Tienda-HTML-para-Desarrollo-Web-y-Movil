const { conectarDB, ObjectId } = require("./db");

// Convierte el documento de Mongo (con _id) al formato que espera el schema (con id string)
function formatearProducto(doc) {
  if (!doc) return null;
  return {
    id: doc._id.toString(),
    nombre: doc.nombre,
    precio: doc.precio,
    descripcion: doc.descripcion || null,
    imagen: doc.imagen || null,
  };
}

const resolvers = {
  Query: {
    // Consultar: trae todos los productos de la coleccion
    productos: async () => {
      const db = await conectarDB();
      const docs = await db.collection("productos").find().toArray();
      return docs.map(formatearProducto);
    },

    // Consultar por id: trae un solo producto
    producto: async (_, { id }) => {
      const db = await conectarDB();
      const doc = await db.collection("productos").findOne({ _id: new ObjectId(id) });
      return formatearProducto(doc);
    },
  },

  Mutation: {
    // Insertar: crea un producto nuevo
    insertarProducto: async (_, { nombre, precio, descripcion, imagen }) => {
      const db = await conectarDB();
      const nuevo = { nombre, precio, descripcion: descripcion || null, imagen: imagen || null };
      const resultado = await db.collection("productos").insertOne(nuevo);
      return formatearProducto({ _id: resultado.insertedId, ...nuevo });
    },

    // Actualizar: modifica los campos enviados de un producto existente
    actualizarProducto: async (_, { id, ...cambios }) => {
      const db = await conectarDB();

      // Solo se actualizan los campos que realmente llegaron en la mutation
      const set = {};
      Object.keys(cambios).forEach((campo) => {
        if (cambios[campo] !== undefined) set[campo] = cambios[campo];
      });

      await db.collection("productos").updateOne(
        { _id: new ObjectId(id) },
        { $set: set }
      );

      const actualizado = await db.collection("productos").findOne({ _id: new ObjectId(id) });
      return formatearProducto(actualizado);
    },

    // Eliminar: borra un producto por id
    eliminarProducto: async (_, { id }) => {
      const db = await conectarDB();
      const resultado = await db.collection("productos").deleteOne({ _id: new ObjectId(id) });
      return resultado.deletedCount === 1;
    },
  },
};

module.exports = resolvers;
