-- payments: intentos de pago y avisos del proveedor
CREATE TABLE IF NOT EXISTS pagos (
    id           TEXT PRIMARY KEY,
    pedido_id    INTEGER NOT NULL,
    user_id      TEXT NOT NULL,
    monto        INTEGER NOT NULL CHECK (monto > 0),
    metodo       TEXT NOT NULL CHECK (metodo IN ('tarjeta', 'transferencia')),
    estado       TEXT NOT NULL CHECK (estado IN ('pendiente', 'aprobado', 'rechazado', 'anulado')),
    checkout_id  TEXT,
    checkout_url TEXT,
    sincronizado INTEGER NOT NULL DEFAULT 0,
    creado       TEXT NOT NULL DEFAULT (datetime('now')),
    actualizado  TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Un pedido tiene a lo mas un pago vivo (pendiente o aprobado).
CREATE UNIQUE INDEX IF NOT EXISTS uq_pago_vivo ON pagos(pedido_id) WHERE estado IN ('pendiente', 'aprobado');

-- Cada aviso del proveedor se procesa una sola vez.
CREATE TABLE IF NOT EXISTS avisos_proveedor (
    evento_id TEXT PRIMARY KEY,
    pago_id   TEXT NOT NULL,
    estado    TEXT NOT NULL,
    recibido  TEXT NOT NULL DEFAULT (datetime('now'))
);
