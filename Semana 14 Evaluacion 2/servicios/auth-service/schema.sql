-- auth: identidades y sesiones. Base propia, separada de clients.
CREATE TABLE IF NOT EXISTS usuarios (
    user_id       TEXT PRIMARY KEY,
    username      TEXT NOT NULL UNIQUE COLLATE NOCASE,
    sal           TEXT NOT NULL,
    hash          TEXT NOT NULL,
    iteraciones   INTEGER NOT NULL,
    roles         TEXT NOT NULL DEFAULT 'user',
    creado        TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Se guarda el hash del token, no el token.
CREATE TABLE IF NOT EXISTS sesiones (
    token_hash TEXT PRIMARY KEY,
    user_id    TEXT NOT NULL REFERENCES usuarios(user_id) ON DELETE CASCADE,
    expira     REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_sesiones_expira ON sesiones(expira);
