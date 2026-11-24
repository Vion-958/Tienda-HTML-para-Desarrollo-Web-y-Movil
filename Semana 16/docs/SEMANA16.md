# ChocoManía — Semana 16: módulo de Pedidos integrado en contenedores

**Desarrollo Web y Móvil · Universidad Andrés Bello**
Vicente Ignacio Ortega · Caso 25. Chocolatería “ChocoManía” – chocolates artesanales
Entrega: lunes 23 de noviembre de 2026

---

## Objetivo

- **¿Qué se pidió?**
    Demostrar un módulo del software integrado, con evidencia de cinco contenedores:
    1. el frontend llama al API Gateway;
    2. el Gateway pide validación y enruta;
    3. el Auth Service valida antes del enrutamiento;
    4. el backend permite o impide la llamada según sus secretos;
    5. el backend consulta o modifica la base de datos.
- **¿Qué se tuvo en cuenta de la reunión con el profesor?**
    Que los secretos se lean desde Vault, que haya pruebas end-to-end y que la entrega no se quede en la encriptación. Por eso, la URL y la clave de la base de cada servicio también se guardan en Vault, y las pruebas end-to-end se ejecutan contra PostgreSQL.
- **¿Qué módulo se demuestra?**
    **Pedidos.** Es el que recorre más contenedores en una sola acción del cliente: sitio → gateway → auth → orders → inventory → postgres.

## Qué cambió

| Archivo | Cambio |
|---|---|
| `servicios/comun/db.py` | Persistencia doble: **PostgreSQL** si `secret/<servicio>` trae `database_url`; si no, SQLite. Traduce el SQL de los servicios (parámetros, fechas, `LIKE`, tipos), mantiene un pool de conexiones y serializa las escrituras de cada servicio. Si la clave de la base cambia en Vault, la relee y se reconecta sin reiniciar. |
| `servicios/comun/bitacora.py` | **Nuevo.** Cada línea de log lleva el `rid` (X-Request-ID) de la solicitud en curso, para seguirla de un contenedor a otro. |
| `servicios/comun/secretos.py`, `seguridad.py` | Registran qué versión de `secret/<servicio>` se leyó y si la credencial del llamador fue **verificada → permitido** o **rechazada → 403**. |
| `servicios/api-gateway/app.py` | Registra cuándo pide validación al Auth Service, su respuesta y a qué backend enruta, con la credencial de Vault que usa. |
| `servicios/auth-service/app.py` | Registra el resultado de la autenticación (login) y de la autorización (introspección de la sesión). |
| `servicios/*/app.py` | Los cinco servicios con base leen su `database_url` desde Vault. |
| `iniciar.py` | Nueva opción `--postgres URL`: crea un rol y un esquema por servicio y guarda la URL de cada uno en Vault. |
| `docker-compose.yml`, `preparar_vault.py`, `.env.example` | Nuevo contenedor `postgres` (16-alpine) con log de escrituras; `vault-init` crea los roles y esquemas. Se quitan los volúmenes SQLite. |
| `crear_env.py` | **Nuevo.** Crea el `.env` de docker compose con claves aleatorias. |
| `pruebas/integracion/test_postgres.py` | **Nuevo.** 4 pruebas de la base: la URL solo está en Vault, cada rol ve solo su esquema, el pedido queda en PostgreSQL y la clave de la base se rota sin reiniciar. |

## Persistencia

- **¿Por qué PostgreSQL?**
    Para que la persistencia sea un contenedor propio, como pide la evidencia 5, y no un archivo dentro de cada servicio. SQLite se mantiene para desarrollar sin Docker y para las pruebas unitarias.
- **¿Cómo se separan los datos de cada servicio?**
    Hay un solo PostgreSQL, con un **esquema por servicio** (`auth`, `inventory`, `orders`, `clients`, `payments`) y un **rol por servicio** (`chocomania_orders`, …), dueño solo de su esquema. Así se conserva la regla de los microservicios: cada uno es dueño de sus datos. El rol de orders recibe `permission denied for schema auth` si intenta leer los usuarios.
- **¿Dónde está la clave de la base?**
    En Vault, como `database_url` dentro de `secret/<servicio>`. Ningún contenedor de servicio la recibe por variable de entorno. Solo `vault-init` conoce la clave del administrador de PostgreSQL, y la usa para crear los roles.
- **¿Hubo que cambiar el SQL de los servicios?**
    No. `comun/db.py` traduce las diferencias entre SQLite y PostgreSQL: `?` → `%s`, `datetime('now')`, `LIKE` sin distinguir mayúsculas, `AUTOINCREMENT` → `IDENTITY` y `BLOB` → `BYTEA`. También entrega las filas con la misma forma (`fila["col"]`). Los datos de prueba se cargan una sola vez.

## Evidencia en los logs

- **¿Cómo se sigue una solicitud entre contenedores?**
    El Gateway genera un `X-Request-ID` y lo envía a cada servicio y en la respuesta al navegador. Cada línea de log empieza con `rid=<id>`, así que basta copiar el valor desde DevTools y filtrar los logs.
- **¿Qué muestra cada contenedor al crear un pedido?**
    El ejemplo es real, capturado con PostgreSQL:

    ```
    gateway   rid=b913… pide validacion de la sesion a Auth Service (POST /introspect)
    auth      rid=b913… Vault secret/auth v1: credencial de gateway verificada -> permitido
    auth      rid=b913… BD postgres auth: SELECT sesiones (1 filas)
    auth      rid=b913… autorizacion: sesion valida usuario=ana (USR-001) roles=user
    gateway   rid=b913… Auth Service: sesion valida user=USR-001 roles=user
    gateway   rid=b913… enruta a orders POST /orders con la credencial token_orders de Vault secret/gateway v1
    orders    rid=b913… Vault secret/orders v1: credencial de gateway verificada -> permitido
    orders    rid=b913… BD postgres orders: INSERT pedidos (1 filas)
    inventory rid=b913… Vault secret/inventory v1: credencial de orders verificada -> permitido
    inventory rid=b913… BD postgres inventory: INSERT reservas (1 filas)
    orders    rid=b913… BD postgres orders: INSERT pedido_items (1 filas)
    orders    rid=b913… pedido creado id=1004 user=USR-001 total=18800
    gateway   rid=b913… user=USR-001 ruta=S07 POST /api/orders -> 201 17ms
    ```

- **¿Y cuando el backend impide la llamada?**
    Una llamada directa a orders, sin pasar por el Gateway y con una credencial falsa:

    ```
    orders rid=4c1e… Vault secret/orders v1: credencial de gateway rechazada -> 403
    ```

- **¿Qué muestra el contenedor de PostgreSQL?**
    Con `log_statement=mod`, cada escritura queda registrada con el rol que la hizo:

    ```
    [chocomania_orders] LOG:  execute <unnamed>: INSERT INTO pedidos (...) VALUES ($1, ...) RETURNING id
    ```

## Pruebas

- **¿Cuántas pruebas hay y dónde corren?**

    | Conjunto | SQLite | PostgreSQL |
    |---|---|---|
    | Unitarias | 79 | 79 |
    | Integración (sistema completo) | 35 | 39 |
    | Navegador (end-to-end) | 8 | 8 |
    | **Total** | **122** | **126** |

    Todas pasan en ambos casos. Las 4 pruebas de la base solo corren con PostgreSQL.
- **¿Cómo se ejecutan contra PostgreSQL?**
    Se define `CHOCOMANIA_POSTGRES` con la URL del administrador y se ejecuta `pytest pruebas -q`. Las pruebas crean y borran sus propios esquemas.

## Limitaciones

- **¿Se probó `docker compose` completo?**
    No en el entorno de desarrollo, que no tiene acceso a los registros de imágenes de Docker. Lo que sí se verificó:
    - El archivo pasa `docker compose config`.
    - `preparar_vault.py` (el paso de `vault-init`) se ejecutó contra Vault y PostgreSQL reales.
    - Todo el sistema corrió sobre PostgreSQL 16, con los mismos roles, esquemas y logs que usa el compose.
- **¿Qué queda pendiente?**
    - Vault en modo dev guarda todo en memoria: si su contenedor se reinicia, hay que volver a ejecutar `docker compose up` para que `vault-init` lo cargue de nuevo.
    - En producción, Vault podría generar las claves de la base con su motor `database` (credenciales dinámicas con vencimiento) en vez de guardarlas como valor fijo.
