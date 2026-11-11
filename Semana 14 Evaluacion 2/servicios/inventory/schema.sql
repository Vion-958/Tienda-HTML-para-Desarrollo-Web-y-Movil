-- inventory: catalogo, stock, imagenes y reservas de stock por pedido
CREATE TABLE IF NOT EXISTS productos (
    id            TEXT PRIMARY KEY,
    nombre        TEXT NOT NULL UNIQUE COLLATE NOCASE,
    descripcion   TEXT NOT NULL,
    precio        INTEGER NOT NULL CHECK (precio BETWEEN 100 AND 10000000),
    categoria     TEXT NOT NULL,
    stock         INTEGER NOT NULL CHECK (stock >= 0),
    ingredientes  TEXT NOT NULL DEFAULT '',
    alergenos     TEXT NOT NULL DEFAULT '[]',
    activo        INTEGER NOT NULL DEFAULT 1,
    creado_por    TEXT,
    creado        TEXT NOT NULL DEFAULT (datetime('now')),
    actualizado   TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS producto_tags (
    producto_id TEXT NOT NULL REFERENCES productos(id) ON DELETE CASCADE,
    tag         TEXT NOT NULL,
    PRIMARY KEY (producto_id, tag)
);

-- Una imagen es una URL externa (datos de prueba) o un archivo subido (datos).
CREATE TABLE IF NOT EXISTS imagenes (
    id          TEXT PRIMARY KEY,
    producto_id TEXT NOT NULL REFERENCES productos(id) ON DELETE CASCADE,
    posicion    INTEGER NOT NULL,
    url         TEXT,
    mime        TEXT,
    datos       BLOB,
    CHECK (url IS NOT NULL OR datos IS NOT NULL)
);

-- Stock apartado por un pedido. estado: reservada | confirmada | liberada
CREATE TABLE IF NOT EXISTS reservas (
    pedido_id   INTEGER NOT NULL,
    producto_id TEXT NOT NULL REFERENCES productos(id),
    cantidad    INTEGER NOT NULL CHECK (cantidad > 0),
    estado      TEXT NOT NULL DEFAULT 'reservada',
    actualizado TEXT NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (pedido_id, producto_id)
);

CREATE INDEX IF NOT EXISTS idx_productos_categoria ON productos(categoria);
CREATE INDEX IF NOT EXISTS idx_tags_tag ON producto_tags(tag);
