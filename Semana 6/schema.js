const schema = `
  type Producto {
    id: ID!
    nombre: String!
    precio: Int!
    descripcion: String
    imagen: String
  }

  type Query {
    productos: [Producto!]!
    producto(id: ID!): Producto
  }

  type Mutation {
    insertarProducto(
      nombre: String!
      precio: Int!
      descripcion: String
      imagen: String
    ): Producto!

    actualizarProducto(
      id: ID!
      nombre: String
      precio: Int
      descripcion: String
      imagen: String
    ): Producto

    eliminarProducto(id: ID!): Boolean!
  }
`;

module.exports = schema;
