const fastify = require("fastify")({ logger: true });
const mercurius = require("mercurius");

const schema = require("./schema");
const resolvers = require("./resolvers");

fastify.register(mercurius, {
  schema,
  resolvers,
  graphiql: true, // habilita el explorador visual en /graphiql
});

const PORT = process.env.PORT || 4000;

fastify.listen({ port: PORT, host: "0.0.0.0" }, (err) => {
  if (err) {
    fastify.log.error(err);
    process.exit(1);
  }
  console.log(`Servidor GraphQL corriendo en http://localhost:${PORT}/graphiql`);
});
