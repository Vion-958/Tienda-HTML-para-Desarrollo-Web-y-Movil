# ChocoManía — Semana 16: módulo integrado en contenedores

Tienda online ChocoManía con backend de microservicios integrado al frontend responsivo.
Esta entrega demuestra el **módulo de Pedidos** integrado en contenedores: frontend → API Gateway → Auth Service → backends que verifican sus secretos en Vault → **PostgreSQL**, con un esquema y un usuario de base por servicio cuya URL también vive en Vault. Cada paso queda en el log de su contenedor con el mismo `X-Request-ID`.

- Qué cambió en esta semana: **[docs/SEMANA16.md](docs/SEMANA16.md)** (Semana 15: [docs/SEMANA15.md](docs/SEMANA15.md))
- Informe de la Evaluación 2 (base de esta entrega): [docs/INFORME.md](docs/INFORME.md)

```
Navegador ──cookie HttpOnly──> API Gateway :8000 ──> Sitio PHP :8080
                                   │  rutas, roles, límites, X-Request-ID
                                   ├──> Auth Service :8100      (esquema auth)
                                   ├──> Vault :8200             (secretos y URL de base de cada servicio)
                                   ├──> inventory :9101         (esquema inventory)
                                   ├──> orders :9102  ──> inventory   (esquema orders)
                                   ├──> clients :9103           (esquema clients)
                                   ├──> payments :9104 ──> orders, pasarela
                                   └──> GraphQL Gateway :9200 ──> orders, inventory, payments, clients
Pasarela sandbox :9300 (proveedor externo simulado) ──aviso firmado──> API Gateway
PostgreSQL :5432  un esquema y un rol por servicio (sin PostgreSQL, cada servicio usa SQLite)
```

## Requisitos

- Python 3.12 o superior
- PHP 8 (`php -v`). Si usas XAMPP, sirve `chocomania-frontend` en el puerto 8080 y usa `--sin-php`.
- Docker Desktop para la versión en contenedores o para usar HashiCorp Vault y PostgreSQL con `iniciar.py`.

## Contenedores (docker compose)

```powershell
cd "Semana 16"
python crear_env.py                 # .env con claves aleatorias (solo la primera vez)
docker compose up --build -d
docker compose logs -f gateway auth orders inventory postgres sitio
```

Abre **http://localhost:8000**. `docker compose down` detiene todo; `docker compose down -v` además borra la base.

| Contenedor | Rol en la demostración |
|---|---|
| `sitio` | Frontend PHP; el navegador lo recibe a través del Gateway |
| `gateway` | Única puerta de entrada: valida la sesión con `auth`, enruta y firma cada llamada con su credencial de Vault |
| `auth` | Valida que quien pregunta sea el Gateway y que la sesión exista |
| `orders`, `inventory`, `clients`, `payments`, `graphql` | Backends: verifican la credencial del llamador contra Vault y usan su esquema de PostgreSQL |
| `vault` | HashiCorp Vault 1.17: credenciales entre servicios y URL de la base de cada uno |
| `vault-init` | Crea los roles y esquemas en PostgreSQL y carga Vault; termina en `exited (0)` |
| `postgres` | PostgreSQL 16 con `log_statement=mod`: su log muestra cada escritura y el rol que la hizo |
| `pasarela` | Proveedor de pagos simulado (puerto 9300) |

## Iniciar sin contenedores

```powershell
cd "Semana 16"
python -m venv .venv
.venv\Scripts\Activate.ps1               # Linux/macOS: source .venv/bin/activate
pip install -r requirements-dev.txt
python iniciar.py
```

Abre **http://127.0.0.1:8000**. Para detener todo, presiona **Ctrl+C** en la terminal de `iniciar.py`. Las cuentas para entrar están en [Cuentas y datos de prueba](#cuentas-y-datos-de-prueba).

Opciones:

```powershell
python iniciar.py --vault-docker      # HashiCorp Vault real en Docker (hashicorp/vault:1.17), como en la guía
python iniciar.py --postgres postgresql://postgres:clave@127.0.0.1:5432/postgres   # PostgreSQL en vez de SQLite
python iniciar.py --reiniciar-datos   # borra las bases y recarga los datos de prueba
python iniciar.py --sin-php           # el sitio ya corre aparte en :8080
```

Los logs de cada proceso quedan en `logs/`. Sin `--postgres`, cada servicio usa su propio archivo SQLite; el código y el SQL son los mismos.

## Secretos en Vault

`iniciar.py` genera credenciales nuevas en cada arranque, las guarda en Vault y crea **un token de solo lectura por servicio**. Cada servicio recibe únicamente la dirección de Vault y su token; las credenciales nunca pasan por variables de entorno ni quedan en disco.

| Ruta en Vault | La lee | Contiene |
|---|---|---|
| `secret/gateway` | API Gateway | `token_<servicio>` para llamar a cada servicio |
| `secret/auth`, `secret/inventory`, `secret/clients` | cada servicio | `llamador_<origen>`: credenciales que acepta |
| `secret/orders`, `secret/graphql` | cada servicio | las que acepta y las que usa (`token_inventory`, …) |
| `secret/payments` | payments | además, las claves de la pasarela de pago |
| `secret/<servicio>` → `database_url` | auth, inventory, orders, clients, payments | usuario, clave y dirección de su esquema de PostgreSQL |

El token de `orders` no puede leer `secret/payments` (403), ni ningún servicio puede escribir en Vault.

**Rotar una credencial** con el sistema corriendo, sin reiniciar ni cambiar código:

```powershell
python rotar.py orders inventory     # credencial que usa orders para llamar a inventory
python rotar.py --todas              # todas las credenciales entre servicios
```

La rotación tiene dos fases: primero el servicio acepta la credencial nueva y la anterior; después de que todos refrescan su caché (30 s), solo la nueva.

## Cuentas y datos de prueba

El sitio no muestra cuentas ni avisos de prueba para verse como una tienda real. Todo lo necesario para probarlo está aquí.

| Usuario | Contraseña | Rol | Qué trae |
|---|---|---|---|
| `ana` | `1234` | cliente | Pedido #1001 pagado y pedido #1003 pendiente de pago (para probar *Pagar* y *Cancelar*) |
| `ernesto` | `admin123` | administrador | Pedido #1002 por transferencia pendiente (para probar *Confirmar transferencia*) |

También puedes crear una cuenta nueva en *Mi cuenta → Crear una cuenta*. La contraseña debe tener al menos 8 caracteres, con letras y números.

- **Pago con tarjeta:** el checkout lleva a **SandboxPay**, un simulador del proveedor de pagos que corre en el puerto 9300. No pide datos de tarjeta: tiene un botón para aprobar y otro para rechazar.
- **Pago por transferencia:** el pedido queda pendiente hasta que `ernesto` lo confirme en *Gestión de pedidos*.
- **Envío:** despacho a domicilio $3.000, gratis desde $30.000. El retiro en tienda no tiene costo.
- **Datos ficticios:** productos, pedidos, direcciones y teléfonos son de ejemplo. `python iniciar.py --reiniciar-datos` vuelve a este estado inicial.

## Qué probar en el navegador

1. **Catálogo sin sesión**: filtra por categoría y por tags.
2. **Mi cuenta → Crear una cuenta** y luego agrega productos al carrito.
3. **Carrito → Confirmar y pagar** con tarjeta: te lleva a la página de **SandboxPay**. Al aprobar, vuelves a *Mi cuenta* y el pedido aparece **Pagado**. Prueba también rechazar el pago y luego pagar de nuevo.
4. **Transferencia**: muestra los datos de la cuenta. El pedido queda pendiente hasta que el admin confirme.
5. **Cancelar** un pedido pendiente: el stock vuelve al catálogo.
6. **Pedidos Especiales** y **Sobre Nosotros**: los formularios llegan al admin.
7. Entra como **ernesto**:
   - *Gestión de pedidos*: preparar, despachar, entregar, anular y confirmar transferencias.
   - *Solicitudes de clientes*.
   - *Administración de productos*: agregar con imágenes, editar y eliminar.

## Pruebas

Detén `iniciar.py` antes de las pruebas de integración, porque levantan su propio sistema con bases temporales.

```powershell
pytest pruebas/unitarias -q        # 79 pruebas, no necesitan nada corriendo
playwright install chromium        # solo la primera vez
pytest pruebas -q                  # 122 pruebas con SQLite (unitarias + integración + navegador)
$env:CHOCOMANIA_POSTGRES="postgresql://postgres:clave@127.0.0.1:5432/postgres"
pytest pruebas -q                  # 126 pruebas: las mismas sobre PostgreSQL + 4 de la base
python pruebas/carga/carga.py      # prueba de carga -> docs/resultados_carga.md
```

## Estructura

```
Semana 16/
├── iniciar.py                  arranque: PostgreSQL, Vault, secretos, tokens por servicio y procesos
├── rotar.py                    rotación de credenciales en Vault sin reiniciar
├── preparar_vault.py           roles de PostgreSQL y carga de Vault para docker compose (vault-init)
├── crear_env.py                crea el .env de docker compose con claves aleatorias
├── requirements.txt            dependencias versionadas (requirements-dev.txt: + pruebas)
├── docker-compose.yml          alternativa con contenedores y redes separadas
├── servicios/
│   ├── comun/                  secretos desde Vault, identidad entre servicios, PostgreSQL/SQLite, logs
│   ├── api-gateway/            tabla de rutas S01–S22, sesión, roles, límites
│   ├── auth-service/           login, registro, introspección (schema.sql, seed.sql)
│   ├── inventory/              catálogo, imágenes, stock, reservas
│   ├── orders/                 pedidos, estados, historial
│   ├── clients/                perfil, cotizaciones, contacto
│   ├── payments/               pagos, aviso firmado, idempotencia
│   ├── graphql-gateway/        agregación privada (schema.graphql)
│   └── pasarela-sandbox/       proveedor de pagos externo simulado
├── vault-local/                Vault local con la misma API de HashiCorp (sin Docker)
├── chocomania-frontend/        sitio PHP integrado con las APIs
├── mensajeria/                 práctica ActiveMQ/STOMP de la Semana 13
├── pruebas/                    unitarias, integración, navegador y carga
└── docs/
    ├── SEMANA16.md             avance de esta semana (SEMANA15.md: la anterior)
    ├── INFORME.md / INFORME.pdf  informe de la Evaluación 2
    ├── diagramas/              UML, componentes y secuencias (.mmd editables + .svg/.png)
    ├── c4/workspace.dsl        modelo C4 (contexto, contenedores, dinámicas, despliegue)
    ├── evidencias/             capturas y salida de las pruebas
    └── resultados_carga.md
```
