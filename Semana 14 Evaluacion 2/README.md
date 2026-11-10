# ChocoManía — Evaluación 2: backend seguro completo

Tienda online ChocoManía con backend de microservicios integrado al frontend responsivo.
El informe está en **[docs/INFORME.md](docs/INFORME.md)** (también en PDF).

```
Navegador ──cookie HttpOnly──> API Gateway :8000 ──> Sitio PHP :8080
                                   │  rutas, roles, límites, X-Request-ID
                                   ├──> Auth Service :8100      (identity.db)
                                   ├──> Vault :8200             (credenciales del Gateway)
                                   ├──> inventory :9101         (inventory.db)
                                   ├──> orders :9102  ──> inventory
                                   ├──> clients :9103           (clients.db)
                                   ├──> payments :9104 ──> orders, pasarela
                                   └──> GraphQL Gateway :9200 ──> orders, inventory, payments, clients
Pasarela sandbox :9300 (proveedor externo simulado) ──aviso firmado──> API Gateway
```

## Requisitos

- Python 3.12 o superior
- PHP 8 (`php -v`). Si usas XAMPP, sirve `chocomania-frontend` en el puerto 8080 y usa `--sin-php`.
- Docker no es necesario.

## Iniciar

```powershell
cd "Semana 14 - EVALUACION 2"
python -m venv .venv
.venv\Scripts\Activate.ps1               # Linux/macOS: source .venv/bin/activate
pip install -r requirements-dev.txt
python iniciar.py
```

Abre **http://127.0.0.1:8000**. Para detener todo, presiona **Ctrl+C** en la terminal de `iniciar.py`. Las cuentas para entrar están en [Cuentas y datos de prueba](#cuentas-y-datos-de-prueba).

Opciones:

```powershell
python iniciar.py --reiniciar-datos   # borra las bases y recarga los datos de prueba
python iniciar.py --sin-php           # el sitio ya corre aparte en :8080
```

`iniciar.py` genera credenciales nuevas y distintas para cada integración en cada arranque. No quedan en disco ni en el repositorio: el Gateway las lee desde Vault y cada servicio recibe solo las suyas. Los logs de cada proceso quedan en `logs/`.

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
pytest pruebas/unitarias -q        # 68 pruebas, no necesitan nada corriendo
playwright install chromium        # solo la primera vez
pytest pruebas -q                  # las 98 pruebas (unitarias + integración + navegador)
python pruebas/carga/carga.py      # prueba de carga -> docs/resultados_carga.md
```

## Estructura

```
Semana 14 - EVALUACION 2/
├── iniciar.py                  arranque y detención del sistema completo
├── requirements.txt            dependencias versionadas (requirements-dev.txt: + pruebas)
├── docker-compose.yml          alternativa con contenedores y redes separadas
├── servicios/
│   ├── comun/                  SQLite, identidad entre servicios, logs con correlación
│   ├── api-gateway/            tabla de rutas S01–S22, sesión, roles, límites
│   ├── auth-service/           login, registro, introspección (schema.sql, seed.sql)
│   ├── inventory/              catálogo, imágenes, stock, reservas
│   ├── orders/                 pedidos, estados, historial
│   ├── clients/                perfil, cotizaciones, contacto
│   ├── payments/               pagos, aviso firmado, idempotencia
│   ├── graphql-gateway/        agregación privada (schema.graphql)
│   └── pasarela-sandbox/       proveedor de pagos externo simulado
├── vault-local/                Vault de reemplazo sin Docker
├── chocomania-frontend/        sitio PHP integrado con las APIs
├── mensajeria/                 práctica ActiveMQ/STOMP de la Semana 13
├── pruebas/                    unitarias, integración, navegador y carga
└── docs/
    ├── INFORME.md / INFORME.pdf
    ├── diagramas/              UML, componentes y secuencias (.mmd editables + .svg/.png)
    ├── c4/workspace.dsl        modelo C4 (contexto, contenedores, dinámicas, despliegue)
    ├── evidencias/             capturas y salida de las pruebas
    └── resultados_carga.md
```

## Docker (alternativa)

```powershell
copy .env.example .env     # reemplaza cada valor por uno aleatorio
docker compose up --build
```

Los microservicios quedan en una red `internal` sin acceso desde el host. Solo el Gateway (8000) y la pasarela (9300) publican puertos. El arranque verificado de esta entrega es `iniciar.py`.
