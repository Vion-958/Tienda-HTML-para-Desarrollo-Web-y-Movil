# ChocoManía — Semana 9: Autenticación, Autorización, API Gateway, Vault, Backend y Frontend

Aplicación de la guía *"Autenticación, Autorización, API Gateway, Vault,
Backend y Frontend"* a la tienda ChocoManía. Respecto a la Semana 8, el
token fijo del cliente se reemplaza por **usuarios reales con login**,
sesiones en el servidor, **cookie HttpOnly** y **roles**.

```
                              Auth Service :8100
                         (login, introspección, logout)
                                    ^
                     login / logout | introspección
                                    |
Navegador --cookie de sesión--> API Gateway :8000 --identidad + secreto interno--> Backend API :9000
(sitio ChocoManía)              (sirve el sitio)
                                    |
                                    v secretos
                              HashiCorp Vault :8200
```

| Componente | Responsabilidad | No hace |
|---|---|---|
| **Frontend** (`chocomania-frontend/`) | Interacción con el usuario: login, "Mi cuenta", catálogo | No autoriza nada ni guarda el token (no hay `localStorage`) |
| **Auth Service** (`auth-service/`) | Verifica credenciales, emite tokens opacos, introspección y logout | No ejecuta lógica de negocio |
| **API Gateway** (`api-gateway/`) | Valida la sesión, autoriza por rol, enruta y propaga la identidad | No contiene lógica de negocio |
| **Vault** | Guarda los secretos entre servicios | No autentica usuarios |
| **Backend** (`backend-api/`) | Lógica de negocio: catálogo y pedidos | No confía en cualquier cliente: exige el secreto del Gateway |

Usuarios de prueba:

| Usuario | Contraseña | ID | Roles |
|---|---|---|---|
| `ana` | `1234` | USR-001 | `user` |
| `ernesto` | `admin123` | USR-003 | `user`, `admin` |

Las contraseñas no están en texto plano: se guarda un hash PBKDF2-SHA256 con
sal por usuario.

## Estructura

```
Semana 9/
├── auth-service/        auth_service.py  (:8100)
├── backend-api/         backend_api.py   (:9000)
├── api-gateway/         gateway.py       (:8000)
├── chocomania-frontend/ sitio PHP, con la nueva página cuenta.php
├── tests/               pruebas unitarias (pytest)
├── e2e/                 test_stack.py (integración) y test_frontend.py (Playwright)
├── docker-compose.yml
├── .env.example         secretos del laboratorio (copiar a .env)
└── requirements-dev.txt
```

## Opción A: todo con Docker (recomendado)

```powershell
copy .env.example .env          # Linux/macOS: cp .env.example .env
docker compose up --build
```

Luego abre **http://localhost:8000** y entra a **Mi cuenta**.

| Servicio | Dirección |
|---|---|
| Gateway + Frontend | http://localhost:8000 |
| Auth Service | http://localhost:8100 |
| Vault | http://localhost:8200 |
| Backend | http://localhost:9000 |

Verificación:

```bash
curl http://localhost:8000/health
curl http://localhost:8100/health
curl http://localhost:9000/health
```

Los secretos no están en `docker-compose.yml`: se leen de `.env`, que está en
`.gitignore`. El servicio `vault-init` los guarda en Vault al arrancar, y el
Gateway los lee desde Vault. El sitio PHP no publica su puerto, así que solo
se puede llegar a él a través del Gateway.

> Productos y sesiones viven en memoria. Si eliminas productos y quieres
> recuperar el catálogo completo: `docker compose restart backend`.

## Opción B: sin Docker Compose (5 terminales)

Vault igual necesita Docker (como en la Semana 8):

```powershell
docker run --name vault-dev -p 8200:8200 -e VAULT_DEV_ROOT_TOKEN_ID=dev-only-token -d hashicorp/vault
docker exec -e VAULT_ADDR=http://127.0.0.1:8200 -e VAULT_TOKEN=dev-only-token vault-dev vault kv put secret/gateway backend_shared_secret="gateway-api-secret-456" auth_introspection_secret="gateway-auth-secret-789"
```

Un entorno virtual en la carpeta `Semana 9` sirve para todos los servicios:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1                  # Linux/macOS: source .venv/bin/activate
pip install -r requirements-dev.txt
```

Luego, cada servicio en su propia terminal (con el entorno activado):

```powershell
# 1. Auth Service
cd auth-service
$env:AUTH_INTROSPECTION_SECRET="gateway-auth-secret-789"
uvicorn auth_service:app --port 8100

# 2. Backend
cd backend-api
$env:INTERNAL_GATEWAY_SECRET="gateway-api-secret-456"
uvicorn backend_api:app --port 9000

# 3. Sitio PHP (o XAMPP en el puerto 8080)
cd chocomania-frontend
php -S 127.0.0.1:8080

# 4. Gateway
cd api-gateway
$env:VAULT_TOKEN="dev-only-token"
uvicorn gateway:app --port 8000
```

En Linux/macOS, `export VARIABLE=valor` en vez de `$env:VARIABLE="valor"`. El
Gateway usa por defecto `127.0.0.1` para Vault, Auth, Backend y el sitio.

> Abre siempre el sitio en **http://localhost:8000**, no en el 8080. Si lo
> abres directo en el 8080 no existe `/auth/login`, y el catálogo queda en
> modo respaldo.

## Secuencia manual de pruebas

Con `curl` (Git Bash, Linux o macOS). `-c` guarda la cookie y `-b` la envía,
como haría el navegador.

```bash
# A. Backend directo -> 403
curl -i http://localhost:9000/products

# B. Login incorrecto -> 401
curl -i -X POST http://localhost:8000/auth/login -H "Content-Type: application/json" \
  -d '{"username":"ana","password":"incorrecta"}'

# C. Login Ana -> 200 y cookie HttpOnly; luego me, productos y pedidos -> 200
curl -i -c ana.txt -X POST http://localhost:8000/auth/login -H "Content-Type: application/json" \
  -d '{"username":"ana","password":"1234"}'
curl -b ana.txt http://localhost:8000/auth/me
curl -b ana.txt http://localhost:8000/api/products
curl -b ana.txt http://localhost:8000/api/orders

# D. Autorización: Ana intenta eliminar -> 403
curl -i -b ana.txt -X DELETE http://localhost:8000/api/products/choco-1

# E. Administrador: Ernesto elimina -> 200
curl -c ernesto.txt -X POST http://localhost:8000/auth/login -H "Content-Type: application/json" \
  -d '{"username":"ernesto","password":"admin123"}'
curl -i -b ernesto.txt -X DELETE http://localhost:8000/api/products/choco-1

# F. Logout y luego /auth/me -> 401
curl -b ana.txt -c ana.txt -X POST http://localhost:8000/auth/logout
curl -i -b ana.txt http://localhost:8000/auth/me
```

En PowerShell, la sesión se mantiene con `-SessionVariable` / `-WebSession`:

```powershell
Invoke-RestMethod -Method Post http://localhost:8000/auth/login -ContentType "application/json" `
  -Body '{"username":"ana","password":"1234"}' -SessionVariable s
Invoke-RestMethod http://localhost:8000/api/orders -WebSession $s
Invoke-RestMethod -Method Delete http://localhost:8000/api/products/choco-1 -WebSession $s   # error 403
```

Los productos se identifican como `choco-1` … `choco-15` (en la guía, `1`).

En el navegador se puede ver lo mismo en **Mi cuenta**: login, pedidos, el
panel de administración (Ana recibe 403 al eliminar y Ernesto 200) y
**Cerrar sesión**. Con F12 → Application → Cookies se ve `session_token`
marcada como HttpOnly, y `document.cookie` en la consola no la muestra.

## Pruebas automatizadas

```bash
pytest tests -q                    # unitarias: 30 pruebas, no necesitan nada corriendo
pytest e2e/test_stack.py -q        # integración: con el sistema arriba
playwright install chromium        # solo la primera vez
pytest e2e/test_frontend.py --headed
```

- **Unitarias** (`tests/`): login válido e inválido, introspección, token
  revocado y expirado, acceso directo al backend bloqueado, rol `user`
  rechazado y rol `admin` autorizado, pedidos filtrados por usuario, política
  de roles del Gateway y borrado de la cookie.
- **Integración** (`e2e/test_stack.py`): login → cookie → me → products →
  autorización → logout, y comprueba que el token ya no sirve tras el logout.
- **Navegador** (`e2e/test_frontend.py`): login con error, Ana sin permiso
  de eliminar, cookie HttpOnly inaccesible desde JavaScript, catálogo en vivo
  con sesión, logout, y Ernesto eliminando un producto.

> Cada corrida de integración y de navegador elimina un producto (como
> Ernesto). Tras unas 6 corridas conviene reiniciar el backend.

## Matriz de validación

| Ruta | Componente | Protección | Esperado |
|---|---|---|---|
| `/login` | Auth | credenciales | 200 / 401 |
| `/introspect` | Auth | secreto Gateway | 200 / 403 |
| `/logout` | Auth | secreto Gateway | 200 / 403 |
| `/products`, `/orders` | Backend | secreto Gateway + identidad | 200 / 403 |
| `DELETE /products/{id}` | Backend | secreto Gateway + rol admin | 200 / 403 |
| `/auth/login` | Gateway | pública | 200 / 401 |
| `/auth/me` | Gateway | sesión | 200 / 401 |
| `/auth/logout` | Gateway | sesión | 200 |
| `/api/products`, `/api/orders` | Gateway | sesión válida | 200 / 401 |
| `DELETE /api/products/{id}` | Gateway | rol admin | 200 / 403 |
| cualquier ruta, con Auth Service o Vault caídos | Gateway | — | 503 |
| `/api/*` con el Backend caído | Gateway | — | 502 |

## Qué se adaptó respecto a la guía

- **El Gateway también sirve el sitio.** Todo lo que no es `/auth/*` ni
  `/api/*` lo reenvía al servidor PHP. Así el sitio, el login y la API
  comparten origen (`localhost:8000`), la cookie viaja sola y no hace falta
  CORS.
- **El catálogo en vivo exige sesión**, como indica la matriz de la guía.
  Sin sesión, el sitio muestra el catálogo de respaldo de las semanas
  anteriores, para seguir siendo navegable.
- **El Backend vuelve a verificar el rol admin** al eliminar, aunque el
  Gateway ya lo hizo: defensa en profundidad.
- **Pedidos por usuario.** Con la identidad propagada, Ana ve solo sus
  pedidos y Ernesto, como admin, ve todos.
- **Vault caído → 503**, igual que el Auth Service caído. En la Semana 8
  respondía 500; ahora ambos se tratan como dependencia de seguridad no
  disponible.
- **El botón Eliminar se muestra a todos a propósito:** la página no decide
  permisos; quien decide es el servidor (403 para Ana).

## Limitaciones

Vault en modo dev, HTTP sin TLS (la cookie no lleva `Secure`; se activa con
`COOKIE_SECURE=true` bajo HTTPS), y usuarios, sesiones y productos en memoria.
En producción harían falta HTTPS, protección CSRF adicional, rate limiting,
persistencia de sesiones, políticas de Vault de mínimo privilegio y,
eventualmente, OAuth 2.0 / OpenID Connect.
