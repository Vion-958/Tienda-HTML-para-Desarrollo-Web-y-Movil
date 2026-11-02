# ChocoManía — Semana 13: Integración con mensajería asíncrona (broker MQ) y modelo C4

Esta carpeta es autocontenida: trae la tienda completa de la Semana 9 (sitio,
API Gateway, Auth Service, Vault y Backend) y le suma lo nuevo de esta semana:

- **Mensajería asíncrona:** un broker ActiveMQ con un productor y un
  consumidor de pedidos por STOMP, en 4 formatos (texto, ancho fijo, XML y
  JSON). Es la práctica *"Integración: productor y consumidor STOMP"*
  aplicada a ChocoManía.
- **Modelo C4** de toda la arquitectura del semestre, en Structurizr DSL.
- **Mi cuenta ampliada:** el cliente puede cancelar sus pedidos pendientes y
  el administrador puede agregar productos con imágenes, tags, stock,
  ingredientes y alérgenos. Los tags aparecen como filtros en el catálogo.

```
                              Auth Service :8100
                                    ^
                     login / logout | introspección
                                    |
Navegador --cookie de sesión--> API Gateway :8000 --identidad + secreto--> Backend API :9000
(sitio ChocoManía)              (sirve el sitio)
                                    |
                                    v secretos
                              HashiCorp Vault :8200

Productor de pedidos --SEND--> ActiveMQ :61613 --MESSAGE--> Procesador de pedidos
(mensajeria/productor.py)      /queue/chocomania.pedidos      (mensajeria/consumidor.py)
                                         ^                           |
                                         +------- ACK / NACK --------+
```

## Estructura

```
Semana 13/
├── auth-service/        auth_service.py  (:8100)          ┐
├── backend-api/         backend_api.py   (:9000)          │
├── api-gateway/         gateway.py       (:8000)          │ igual que
├── chocomania-frontend/ sitio PHP                         │ la Semana 9
├── tests/               pruebas unitarias del stack       │
├── e2e/                 integración y navegador           ┘
├── mensajeria/                                            ┐
│   ├── productor.py     publica pedidos en 4 formatos     │
│   ├── consumidor.py    escucha la cola, ACK / NACK       │ nuevo en la
│   ├── requirements.txt                                   │ Semana 13
│   └── tests/test_formatos.py                             │
├── c4/workspace.dsl     modelo C4 (Structurizr DSL)       │
├── vault-local/         Vault de reemplazo sin Docker     ┘
├── docker-compose.yml   todo el stack + ActiveMQ
├── .env.example         secretos del laboratorio (copiar a .env)
└── requirements-dev.txt
```

Usuarios de prueba de la tienda:

| Usuario | Contraseña | ID | Roles |
|---|---|---|---|
| `ana` | `1234` | USR-001 | `user` |
| `ernesto` | `admin123` | USR-003 | `user`, `admin` |

## Opción A: todo con Docker (recomendado)

```powershell
copy .env.example .env          # Linux/macOS: cp .env.example .env
docker compose up --build
```

| Servicio | Dirección |
|---|---|
| Tienda (Gateway + sitio) | http://localhost:8000 |
| Consola de ActiveMQ | http://localhost:8161/admin (admin / admin) |
| Auth Service | http://localhost:8100 |
| Vault | http://localhost:8200 |
| Backend | http://localhost:9000 |
| Broker STOMP | localhost:61613 (demo / demo123) |

Verificación:

```bash
curl http://localhost:8000/health
curl http://localhost:8100/health
curl http://localhost:9000/health
```

Si solo quieres la parte de mensajería, basta con el broker:

```powershell
docker compose up -d activemq
```

Los secretos no están en `docker-compose.yml`: se leen de `.env`, que está en
`.gitignore`. El servicio `vault-init` los guarda en Vault al arrancar y el
Gateway los lee desde Vault. El sitio PHP no publica su puerto, así que solo
se llega a él a través del Gateway.

> Productos y sesiones viven en memoria. Si eliminas productos y quieres
> recuperar el catálogo completo: `docker compose restart backend`.

## Opción B: sin Docker Compose

Vault, con Docker:

```powershell
docker run --name vault-dev -p 8200:8200 -e VAULT_DEV_ROOT_TOKEN_ID=dev-only-token -d hashicorp/vault
docker exec -e VAULT_ADDR=http://127.0.0.1:8200 -e VAULT_TOKEN=dev-only-token vault-dev vault kv put secret/gateway backend_shared_secret="gateway-api-secret-456" auth_introspection_secret="gateway-auth-secret-789"
```

**Sin Docker**, usa el Vault local de reemplazo (no necesita instalar nada):

```powershell
cd vault-local
python vault_local.py
```

Entrega los mismos secretos en la misma ruta que el Vault real
(`/v1/secret/data/gateway`, token `dev-only-token`). Es solo para el
laboratorio: no cifra ni tiene políticas.

> **Si el login responde 503**, casi siempre es porque el secreto del Vault
> no coincide con el del Auth Service: el Auth Service rechaza la
> introspección y en la terminal del Gateway aparece `introspect respondio
> 403`. Los valores deben ser exactamente `gateway-auth-secret-789` (Auth) y
> `gateway-api-secret-456` (Backend). Compruébalo con
> `curl -H "X-Vault-Token: dev-only-token" http://127.0.0.1:8200/v1/secret/data/gateway`.

ActiveMQ se puede usar instalado, como en la clase: descargar ActiveMQ
Classic y, desde su carpeta `bin`, ejecutar `activemq start`. Así el broker no
pide usuario y `demo / demo123` se aceptan igual.

Un entorno virtual en la carpeta `Semana 13` sirve para todo:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1                  # Linux/macOS: source .venv/bin/activate
pip install -r requirements-dev.txt
```

> El paquete de mensajería se llama `stomp.py`, no `stomp` (`pip install stomp` falla).
>
> Si ya tenías el entorno de antes, instala lo nuevo del Backend (lo
> necesita para recibir las imágenes del formulario):
> `pip install python-multipart`. Sin él, el Backend no arranca.

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

# 4. Gateway (con Vault o vault_local.py ya corriendo)
cd api-gateway
$env:VAULT_TOKEN="dev-only-token"
uvicorn gateway:app --port 8000
```

En Linux/macOS, `export VARIABLE=valor` en vez de `$env:VARIABLE="valor"`.

> Abre siempre la tienda en **http://localhost:8000**, no en el 8080. Si la
> abres directo en el 8080 no existe `/auth/login`, y el catálogo queda en
> modo respaldo.

## Mensajería asíncrona

El productor y el consumidor no se conocen ni se esperan: el productor deja
el pedido en el broker y termina; el consumidor lo procesa cuando puede. Si el
consumidor está apagado, los pedidos quedan encolados y se procesan apenas se
enciende.

Con el broker arriba (opción A o B), desde la carpeta `mensajeria`:

Terminal 1, el consumidor:

```powershell
cd mensajeria
python consumidor.py
```

Terminal 2, el productor, un formato a la vez:

```powershell
cd mensajeria
python productor.py --formato texto --mensaje "Hola desde ChocoManía"
python productor.py --formato fijo --id 123 --cliente "Ana Perez" --producto choco-3 --monto 12990
python productor.py --formato xml  --id 124 --cliente "Ana Perez" --producto choco-7 --monto 8490
python productor.py --formato json --id 125 --cliente "Begoña Muñoz" --producto choco-1 --monto 15990
```

Lo que muestra el consumidor para el pedido de ancho fijo:

```
[RECIBIDO] formato=fijo
{
  "id": "000123",
  "cliente": "Ana Perez",
  "producto": "choco-3",
  "monto": "0012990.00"
}
-> Pedido #000123 de Ana Perez: choco-3 por $12.990
```

### Prueba de asincronía

1. Detén el consumidor (Ctrl+C).
2. Envía varios pedidos: `python productor.py --formato json --repetir 5`
3. En la consola web (http://localhost:8161/admin → *Queues*) se ven 5
   mensajes pendientes en `chocomania.pedidos`.
4. Enciende el consumidor: procesa los 5 de inmediato, en orden.

### Prueba de mensaje inválido (NACK)

```powershell
python productor.py --formato fijo --crudo "000123Ana"
```

El consumidor responde `[MENSAJE NO VÁLIDO] Registro de ancho fijo inválido:
9 caracteres, se esperan 44` y hace NACK. ActiveMQ no lo da por procesado y
lo termina dejando en la cola de mensajes muertos `ActiveMQ.DLQ` (visible en
la consola web).

El productor también protege el contrato antes de enviar: por ejemplo,
`--formato fijo --cliente "Begoña Muñoz"` se rechaza porque el ancho fijo solo
admite ASCII. En JSON y XML ese mismo nombre viaja sin problema.

### Formatos y contrato

| Formato | `content-type` | Ejemplo del cuerpo |
|---|---|---|
| `texto` | `text/plain` | `Hola desde ChocoManía` |
| `fijo` | `text/plain` | `000123Ana Perez           choco-3 0012990.00` |
| `xml` | `application/xml` | `<pedido><id>124</id><cliente>Ana Perez</cliente>…</pedido>` |
| `json` | `application/json` | `{"id": "125", "cliente": "Begoña Muñoz", …}` |

Cada mensaje lleva además el header `x-formato` y `persistent: true` (el
broker lo guarda en disco). Si falta `x-formato`, el consumidor deduce el
formato por el `content-type`.

**Contrato de ancho fijo (44 caracteres, solo ASCII):**

| Posición | Campo | Largo | Regla |
|---|---|---|---|
| 0–5 | ID | 6 | dígitos, ceros a la izquierda |
| 6–25 | CLIENTE | 20 | relleno con espacios a la derecha |
| 26–33 | PRODUCTO | 8 | `choco-1` … `choco-15`, relleno a la derecha |
| 34–43 | MONTO | 10 | `0000000.00` |

## Secuencia manual de pruebas de la tienda

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

En el navegador se ve lo mismo en **Mi cuenta**: login, pedidos y **Cerrar
sesión**. El panel de administración de productos solo aparece para el rol
`admin` (Ernesto). Ocultarlo a Ana es solo presentación: si ella llama a
`DELETE /api/products/...` igual recibe 403, porque quien autoriza es el
servidor (paso D).

## Cancelar pedidos y agregar productos

### Cliente: cancelar un pedido

En **Mi cuenta → Mis pedidos**, cada pedido **pendiente** propio muestra un
botón **Cancelar**. Al confirmar, el pedido queda como *Cancelado* y las
unidades vuelven al stock del catálogo.

| Caso | Respuesta |
|---|---|
| Pedido propio pendiente | 200, queda `cancelled` |
| Pedido ya cancelado | 409 |
| Pedido pagado | 409: hay que contactar a la tienda |
| Pedido de otro usuario o inexistente | 404 (no revela que existe) |

Ernesto, como admin, ve todos los pedidos, pero el botón solo aparece en
los suyos: un pedido lo cancela quien lo hizo.

### Administrador: agregar un producto

En **Mi cuenta → Administración de productos → + Agregar producto**:

| Campo | Regla |
|---|---|
| Nombre * | 3 a 80 caracteres, no repetido |
| Categoría * | 2 a 30 caracteres; sugiere las existentes o se escribe una nueva |
| Precio (CLP) * | entero entre $100 y $10.000.000 |
| Stock * | entero entre 0 y 9999 |
| Descripción * | 10 a 500 caracteres |
| Tags | hasta 8, separados por coma; se guardan en minúsculas y sin repetir |
| Ingredientes | hasta 300 caracteres |
| Alérgenos | gluten, lácteos, huevo, frutos secos, soya |
| Imágenes * | 1 a 5, JPG/PNG/WEBP, hasta 2 MB cada una; la primera es la portada |

La página valida antes de enviar, pero quien decide es el Backend, que repite
todas las reglas y devuelve los errores por campo (400). Las imágenes se
reconocen por su contenido (los primeros bytes del archivo), no por el
nombre ni por el tipo que declara el navegador: un `.exe` renombrado a
`.png` se rechaza.

El formulario viaja como `multipart/form-data`: navegador → Gateway (exige
rol `admin` para `POST /api/products`) → Backend. Las imágenes quedan en
memoria del Backend y se sirven en `/api/images/{id}`, también a través del
Gateway y con sesión.

El producto nuevo aparece al instante en el catálogo. Ahí, el panel **Filtrar
por tags** permite combinar tags (el producto debe tenerlos todos), y la
página del producto muestra todas sus imágenes como galería, los tags, el
stock bajo ("¡Quedan 3!" o "Agotado") y sus ingredientes y alérgenos.

> Igual que los productos y pedidos, las imágenes viven en memoria: al
> reiniciar el Backend se pierden.

### Rutas nuevas

| Ruta (vía Gateway) | Protección | Respuestas |
|---|---|---|
| `POST /api/orders/{id}/cancel` | sesión, dueño del pedido | 200 / 404 / 409 |
| `POST /api/products` | rol `admin` (Gateway y Backend) | 201 / 400 / 403 |
| `GET /api/images/{id}` | sesión | 200 / 404 |

## Pruebas automatizadas

```bash
pytest tests mensajeria/tests -q   # unitarias: 72 pruebas, sin nada corriendo
pytest e2e/test_stack.py -q        # integración: con la tienda arriba
playwright install chromium        # solo la primera vez
pytest e2e/test_frontend.py --headed
```

- **Stack** (`tests/`): login, introspección, sesiones revocadas y vencidas,
  backend bloqueado sin el secreto, roles `user` y `admin`, pedidos por
  usuario.
- **Pedidos y productos** (`tests/test_productos_pedidos.py`): cancelación
  (propio, pagado, ajeno, repetido), stock, creación de productos con una o
  varias imágenes, cada validación del formulario y archivos falsos o
  demasiado grandes.
- **Navegador** (`e2e/test_frontend.py`): además de lo anterior, Ana cancela
  un pedido y Ernesto agrega un producto con dos imágenes, lo encuentra con
  el filtro de tags y revisa su página.
- **Mensajería** (`mensajeria/tests/`): lo que serializa el productor lo
  deserializa igual el consumidor en los 4 formatos, y ambos lados rechazan
  lo que no cumple el contrato. No necesitan el broker.

> Cada corrida de integración y de navegador elimina un producto (como
> Ernesto). Tras unas 6 corridas conviene reiniciar el backend.

## Modelo C4 (`c4/workspace.dsl`)

Abre https://playground.structurizr.com, pega el contenido de
`workspace.dsl` y presiona *Render*. O con Structurizr Lite:

```powershell
cd c4
docker run -it --rm -p 8080:8080 -v "${PWD}:/usr/local/structurizr" structurizr/lite
```

y abre http://localhost:8080 (detén antes la tienda si usa el 8080).

| Vista | Qué muestra |
|---|---|
| `C1_Contexto` | Visitante, Cliente y Administrador con la Tienda ChocoManía |
| `C2_Contenedores` | Todos los contenedores: sitio, Gateway, Auth, Vault, Backend, almacenes, GraphQL, broker, productor y consumidor |
| `C2_Catalogo` | Vista focalizada del recorrido de una consulta al catálogo |
| `C2_Administracion` | Vista focalizada del administrador agregando o eliminando un producto |
| `C2_Mensajeria` | Vista focalizada de la integración asíncrona |
| `Dinamica_Login` | Paso a paso: login y consulta de pedidos |
| `Dinamica_Pedido_Asincrono` | Paso a paso: SEND → MESSAGE → ACK/NACK |

El modelo representa lo que existe hoy en el repositorio, no un sistema
ideal: los almacenes de datos son en memoria (Auth y Backend), la API GraphQL
de la Semana 7 aparece con línea punteada porque todavía no pasa por el
Gateway, y el broker aún no está conectado al Backend. Conectar el Backend
como productor real (publicar cada pedido creado) sería el siguiente paso.

## Qué se adaptó respecto a la práctica

- **Pedidos de ChocoManía:** se agregó el campo `producto` (los mismos ids
  `choco-1` … `choco-15` del Backend), así que el contrato fijo pasó de 36 a
  44 caracteres. La cola se llama `/queue/chocomania.pedidos`.
- **Validación de negocio en el consumidor:** además de revisar el formato,
  cada pedido debe traer todos los campos, un producto válido y un monto no
  negativo. Si no, NACK.
- **Prefetch de ActiveMQ:** se usa `activemq.prefetchSize: 1` (en la práctica
  aparece `prefetch-count`, que es el nombre en RabbitMQ). Así el broker
  entrega un pedido a la vez y espera su ACK.
- **`--repetir` y `--crudo`** en el productor, para mostrar la cola acumulando
  pedidos y para probar el NACK.
- **Correcciones menores:** el puerto se recibe como número (`type=int`), se
  corrigió la variable del `except` del productor (`excc` → `exc`) y se
  muestra un mensaje claro si el broker no está arriba.
- **Un solo `docker-compose.yml`:** la tienda de la Semana 9 y ActiveMQ se
  levantan juntos; el usuario del broker (`demo / demo123`) se lee de `.env`.

## Limitaciones

Tienda: Vault en modo dev, HTTP sin TLS y usuarios, sesiones y productos en
memoria. Mensajería: broker con usuario de laboratorio y sin TLS, consumidor
único y sin idempotencia (si un pedido se reentrega, se procesaría dos
veces). En producción harían falta HTTPS y STOMP sobre TLS, credenciales del
broker en Vault, persistencia real, una política de reentrega definida y una
clave de idempotencia por pedido.
