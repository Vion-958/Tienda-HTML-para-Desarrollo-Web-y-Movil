# ChocoManía GraphQL - Fastify + MongoDB

Practica de GraphQL usando **Fastify** como servidor, **mercurius** como adaptador
GraphQL, y **MongoDB** como base de datos. Implementa las 5 operaciones sobre la
coleccion `productos`: insertar, consultar (todos), consultar por id, actualizar
y eliminar.

## Estructura

- `db.js` - conexion a MongoDB.
- `schema.js` - typeDefs: define el tipo `Producto`, las `Query` y las `Mutation`.
- `resolvers.js` - implementa cada operacion contra MongoDB.
- `server.js` - levanta Fastify y registra el plugin de GraphQL (mercurius).
- `seed.js` - carga productos de ejemplo (los mismos de la pagina web) en Mongo.

## Requisitos

- Node.js instalado.
- MongoDB corriendo localmente (`mongod`), escuchando en el puerto por defecto
  27017. Si usas MongoDB Compass, con que el servicio este activo basta.

## Pasos para correrlo

```bash
npm install
node seed.js
node server.js
```

Abre `http://localhost:4000/graphiql` en el navegador: ahi puedes escribir
las queries y mutations de forma visual, sin Postman ni curl.

Si tu MongoDB corre en otra direccion, puedes indicarla asi:

```bash
MONGO_URI="mongodb://localhost:27017" MONGO_DB="chocomania" node server.js
```

## Ejemplos de las 5 operaciones

### 1. Consultar (todos los productos)

```graphql
query {
  productos {
    id
    nombre
    precio
  }
}
```

### 2. Consultar por id

Reemplaza `"ID_AQUI"` por un id real que te devuelva la consulta anterior.

```graphql
query {
  producto(id: "ID_AQUI") {
    id
    nombre
    precio
    descripcion
  }
}
```

### 3. Insertar

```graphql
mutation {
  insertarProducto(
    nombre: "Trufas de chocolate"
    precio: 5200
    descripcion: "Caja de 6 trufas rellenas."
  ) {
    id
    nombre
    precio
  }
}
```

### 4. Actualizar

Solo se actualizan los campos que envies; el resto queda igual.

```graphql
mutation {
  actualizarProducto(id: "ID_AQUI", precio: 5900) {
    id
    nombre
    precio
  }
}
```

### 5. Eliminar

```graphql
mutation {
  eliminarProducto(id: "ID_AQUI")
}
```

Devuelve `true` si se elimino correctamente.

## Notas

- Los ids son los `_id` que genera MongoDB automaticamente (ObjectId), convertidos
  a texto para que se vean como un `ID` normal en GraphQL.
- Este proyecto solo cubre la entidad `Producto`. Si necesitas lo mismo para
  `Servicio`, se replica exactamente el mismo patron: agregar el tipo en
  `schema.js`, y las mismas 5 operaciones en `resolvers.js` pero apuntando a
  la coleccion `servicios`.
