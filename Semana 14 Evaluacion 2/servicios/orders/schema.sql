-- orders: pedidos, su detalle y el historial de estados
CREATE TABLE IF NOT EXISTS pedidos (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id      TEXT NOT NULL,
    estado       TEXT NOT NULL,
    entrega      TEXT NOT NULL CHECK (entrega IN ('retiro', 'delivery')),
    direccion    TEXT NOT NULL DEFAULT '',
    comuna       TEXT NOT NULL DEFAULT '',
    nota         TEXT NOT NULL DEFAULT '',
    metodo_pago  TEXT NOT NULL CHECK (metodo_pago IN ('tarjeta', 'transferencia')),
    subtotal     INTEGER NOT NULL DEFAULT 0,
    costo_envio  INTEGER NOT NULL DEFAULT 0,
    total        INTEGER NOT NULL DEFAULT 0,
    pago_id      TEXT,
    creado       TEXT NOT NULL DEFAULT (datetime('now')),
    actualizado  TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Copia de nombre y precio al comprar; el historial no cambia.
CREATE TABLE IF NOT EXISTS pedido_items (
    pedido_id       INTEGER NOT NULL REFERENCES pedidos(id) ON DELETE CASCADE,
    producto_id     TEXT NOT NULL,
    nombre          TEXT NOT NULL,
    precio_unitario INTEGER NOT NULL CHECK (precio_unitario > 0),
    cantidad        INTEGER NOT NULL CHECK (cantidad > 0),
    PRIMARY KEY (pedido_id, producto_id)
);

CREATE TABLE IF NOT EXISTS pedido_eventos (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    pedido_id       INTEGER NOT NULL REFERENCES pedidos(id) ON DELETE CASCADE,
    estado_anterior TEXT,
    estado_nuevo    TEXT NOT NULL,
    actor           TEXT NOT NULL,
    motivo          TEXT NOT NULL DEFAULT '',
    creado          TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_pedidos_usuario ON pedidos(user_id, id);
CREATE INDEX IF NOT EXISTS idx_pedidos_estado ON pedidos(estado);
