const schema = `
  type Producto {
    id: ID!
    nombre: String!
    precio: Int!
    descripcion: String
    imagen: String
  }

  type Query {
    """Consultar: trae todos los productos"""
    productos: [Producto!]!

    """Consultar por id: trae un solo producto segun su id de Mongo"""
    producto(id: ID!): Producto
  }

  type Mutation {
    """Insertar: crea un producto nuevo"""
    insertarProducto(
      nombre: String!
      precio: Int!
      descripcion: String
      imagen: String
    ): Producto!

    """Actualizar: modifica un producto existente por id"""
    actualizarProducto(
      id: ID!
      nombre: String
      precio: Int
      descripcion: String
      imagen: String
    ): Producto

    """Eliminar: borra un producto por id"""
    eliminarProducto(id: ID!): Boolean!
  }
`;

module.exports = schema;
