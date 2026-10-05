# ChocoManía — Semana 8: API Gateway con FastAPI y HashiCorp Vault

Aplicación del laboratorio *"API Gateway local con FastAPI y HashiCorp Vault"*
a la tienda ChocoManía. El sitio ya no habla directo con el backend: toda
solicitud entra por un **API Gateway**, que valida un Bearer token contra
secretos guardados en **Vault** y solo entonces la reenvía al backend, que
está en otro host.

```
                       HashiCorp Vault :8200
                    (client_token + backend_shared_secret)
                                 ^
                                 | consulta secretos
                                 |
Sitio web / script --Bearer--> API Gateway :8000 --X-Gateway-Secret--> Backend API :9000
                               (HOST A)                                 (HOST B)
                                 |
                                 v
                  401 token inválido / 502 backend caído / 500 Vault caído
```

## Estructura

| Carpeta | Host | Qué contiene |
|---|---|---|
| `backend-api/` | HOST B | `backend_api.py`: API REST de la tienda (`/products`, `/products/{id}`, `/orders`). Rechaza con 403 toda llamada sin la credencial interna del Gateway. |
| `api-gateway/` | HOST A | `gateway.py`: Gateway seguro (Bearer token + Vault + enrutamiento). `pruebas.py`: matriz de pruebas automática. |
| `chocomania-frontend/` | cualquiera | El sitio de la Semana 7, con `js/api.js` adaptado para leer el catálogo **a través del Gateway**. |

Puertos: Gateway `8000`, Vault `8200` (ambos en HOST A), Backend `9000` (HOST B).

## Requisitos

- Python 3.11 o superior y `pip` en ambos hosts.
- Docker en HOST A (para Vault).
- Conectividad entre los hosts y el firewall abierto en los puertos usados.

Las IP de ejemplo son `192.168.1.10` (HOST A) y `192.168.1.20` (HOST B).
Reemplázalas por las reales (`ipconfig` en Windows, `ip a` en Linux).

> **¿Solo un computador?** Funciona igual: corre todo en la misma máquina y
> usa `http://127.0.0.1:9000` como `BACKEND_URL`. Lo único que se pierde es
> la demostración de "otro host".

## Paso 1: comprobar conectividad

Desde HOST A: `ping 192.168.1.20` · Desde HOST B: `ping 192.168.1.10`

## Paso 2: backend en HOST B

```powershell
cd backend-api
python -m venv .venv
.venv\Scripts\Activate.ps1            # Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt

$env:INTERNAL_GATEWAY_SECRET="gateway-api-secret-456"
# Linux/macOS: export INTERNAL_GATEWAY_SECRET="gateway-api-secret-456"

uvicorn backend_api:app --host 0.0.0.0 --port 9000
```

Comprobar que el acceso directo queda bloqueado (desde HOST A):

```powershell
curl http://192.168.1.20:9000/products
# 403 {"detail":"Solicitud no autorizada desde Gateway"}

curl -H "X-Gateway-Secret: gateway-api-secret-456" http://192.168.1.20:9000/products
# 200, con el catálogo
```

> En PowerShell, `curl` puede ser un alias de `Invoke-WebRequest`. Usa
> `curl.exe` para obtener el mismo comportamiento que en la guía.

## Paso 3: Vault en HOST A

```powershell
docker run --name vault-dev -p 8200:8200 -e VAULT_DEV_ROOT_TOKEN_ID=dev-only-token -d hashicorp/vault
```

Guardar los dos secretos (identidad del cliente e identidad del Gateway):

```powershell
docker exec -e VAULT_ADDR=http://127.0.0.1:8200 -e VAULT_TOKEN=dev-only-token vault-dev vault kv put secret/gateway client_token="student-token-123" backend_shared_secret="gateway-api-secret-456"

docker exec -e VAULT_ADDR=http://127.0.0.1:8200 -e VAULT_TOKEN=dev-only-token vault-dev vault kv get secret/gateway
```

> Vault en modo *dev* es solo para el laboratorio: guarda todo en memoria,
> y si el contenedor se reinicia hay que volver a cargar los secretos.

## Paso 4: Gateway en HOST A

```powershell
cd api-gateway
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt

$env:VAULT_ADDR="http://127.0.0.1:8200"
$env:VAULT_TOKEN="dev-only-token"
$env:BACKEND_URL="http://192.168.1.20:9000"
# Linux/macOS: export VAULT_ADDR=... (igual con las otras dos)

uvicorn gateway:app --host 0.0.0.0 --port 8000
```

El Gateway no tiene ningún secreto de negocio en el código: solo sabe dónde
está Vault y con qué token consultarlo.

## Paso 5: probar los escenarios de seguridad

Con todo corriendo, en HOST A (otra terminal, mismo entorno virtual):

```powershell
$env:BACKEND_URL="http://192.168.1.20:9000"
python pruebas.py
```

Salida esperada: `9/9 pruebas con el resultado esperado`.

### Matriz de pruebas

| N° | Prueba | Resultado esperado | Código |
|---|---|---|---|
| 1 | Gateway sin token | Rechazada antes de llegar al backend | 401 |
| 2 | Gateway con token falso | Token rechazado por el Gateway | 401 |
| 3 | Gateway con token válido | Reenviada al backend (`/products`, `/products/{id}`, `/orders`, `POST /orders`) | 200 / 201 |
| 4 | Acceso directo al backend sin secreto | Backend rechaza la petición | 403 |
| 5 | Vault apagado (`docker stop vault-dev`) | Gateway no puede validar credenciales | 500 controlado |
| 6 | Backend apagado (Ctrl+C en HOST B) | Gateway detecta backend no disponible | 502 |
| 7 | Rotación del token en Vault | El token anterior deja de funcionar | 401 / 200 |
| 8 | Secreto interno incorrecto | Backend rechaza la llamada | 403 |
| Extra | Cliente manda su propio `X-Gateway-Secret` | El Gateway lo ignora y exige Bearer | 401 |

Las pruebas 5 y 6 son manuales: apaga el servicio y vuelve a correr la prueba 3.

### Prueba 7: rotar el token sin tocar código

```powershell
docker exec -e VAULT_ADDR=http://127.0.0.1:8200 -e VAULT_TOKEN=dev-only-token vault-dev vault kv put secret/gateway client_token="nuevo-token-789" backend_shared_secret="gateway-api-secret-456"

python pruebas.py --token nuevo-token-789 --token-anterior student-token-123
```

El token anterior pasa a dar 401 y el nuevo da 200, sin reiniciar el
Gateway: lee Vault en cada solicitud.

## Paso 6: el sitio ChocoManía consume el Gateway

`chocomania-frontend/js/api.js` ahora pide el catálogo a
`GET /api/products` y el detalle a `GET /api/products/{id}` del Gateway,
con `Authorization: Bearer <token>`. Por defecto usa:

- Gateway: `http://localhost:8000`
- Token: `student-token-123`

Si el Gateway está en otra máquina, o si rotaste el token, se puede
cambiar sin tocar `api.js`, agregando esto antes de `<script src="js/api.js">`:

```html
<script>window.CHOCO_CONFIG = { gatewayUrl: "http://192.168.1.10:8000", clientToken: "nuevo-token-789" };</script>
```

Para levantar el sitio (o con XAMPP, copiando la carpeta a `htdocs`):

```powershell
cd chocomania-frontend
php -S localhost:8080
```

En la consola del navegador (F12) aparece de dónde salió el catálogo:

- `Catálogo cargado vía API Gateway` → el flujo seguro funciona.
- `El Gateway rechazó el token (401)` → el token del sitio no coincide con Vault.
- `Gateway no disponible: usando catálogo de respaldo` → el sitio sigue navegable con los datos locales.

El Gateway habilita CORS para que el navegador pueda llamarlo desde otro
origen. Por defecto acepta cualquiera; para restringirlo:
`$env:CORS_ORIGINS="http://localhost:8080"`.

## Paso 7 (opcional): restringir la red

El header `X-Gateway-Secret` protege a nivel de aplicación, pero un diseño
más fuerte también limita quién puede abrir conexión al puerto 9000:

```bash
sudo ufw insert 1 allow from 192.168.1.10 to any port 9000 proto tcp
```

En Windows: Firewall de Windows → Reglas de entrada → nueva regla TCP 9000
con dirección remota `192.168.1.10`.

## Qué se adaptó respecto a la guía

- El backend expone los productos de ChocoManía (los mismos 15 del catálogo
  de la Semana 7) en vez de Notebook/Monitor, y los pedidos de la tienda.
- Se agregó `GET /products/{id}` (para la página de detalle) y
  `POST /orders`, para mostrar que el Gateway también reenvía escrituras.
- El Gateway maneja la caída de Vault como un 500 controlado (la guía solo
  cubría una respuesta distinta de 200), e incluye CORS para el sitio web.
- La comparación de secretos usa bytes, para que tokens con tildes u otros
  caracteres no ASCII se rechacen con 401 en vez de provocar un error.

## Limitaciones

- En un sitio web, el token del cliente queda visible en el navegador.
  Representa la identidad del "cliente web"; el secreto interno
  Gateway–Backend nunca llega al navegador.
- Un solo token para todos los clientes: no distingue roles. La actividad de
  cierre de la guía (usuario/administrador, 401 vs 403) sería la extensión.
- Vault en modo dev, HTTP sin TLS y datos en memoria: no es un patrón de
  producción. Lo siguiente sería JWT/OAuth2, HTTPS y mTLS entre servicios.
