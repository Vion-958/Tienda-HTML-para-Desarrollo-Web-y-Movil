-- clients: perfil y datos de contacto. Datos personales (restringidos).
CREATE TABLE IF NOT EXISTS clientes (
    user_id     TEXT PRIMARY KEY,
    nombre      TEXT NOT NULL,
    email       TEXT NOT NULL UNIQUE COLLATE NOCASE,
    telefono    TEXT NOT NULL DEFAULT '',
    direccion   TEXT NOT NULL DEFAULT '',
    comuna      TEXT NOT NULL DEFAULT '',
    creado      TEXT NOT NULL DEFAULT (datetime('now')),
    actualizado TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Solicitudes de cotizacion (Pedidos Especiales) y mensajes de contacto.
CREATE TABLE IF NOT EXISTS solicitudes (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    tipo            TEXT NOT NULL CHECK (tipo IN ('cotizacion', 'contacto')),
    nombre          TEXT NOT NULL DEFAULT '',
    email           TEXT NOT NULL,
    telefono        TEXT NOT NULL DEFAULT '',
    asunto          TEXT NOT NULL,
    fecha_requerida TEXT NOT NULL DEFAULT '',
    cantidad        TEXT NOT NULL DEFAULT '',
    mensaje         TEXT NOT NULL,
    user_id         TEXT,
    estado          TEXT NOT NULL DEFAULT 'nueva' CHECK (estado IN ('nueva', 'respondida')),
    creado          TEXT NOT NULL DEFAULT (datetime('now'))
);
