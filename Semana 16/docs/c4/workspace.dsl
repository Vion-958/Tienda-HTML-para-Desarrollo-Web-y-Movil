/*
 * ChocoMania - Modelo C4 de la Evaluacion 2 (Structurizr DSL)
 * Abrir en https://playground.structurizr.com o con Structurizr Lite.
 */
workspace "ChocoMania" "Backend seguro completo de la tienda ChocoMania" {

    !identifiers hierarchical

    model {
        visitante = person "Visitante" "Consulta el catalogo sin iniciar sesion y envia cotizaciones."
        cliente = person "Cliente" "Compra, paga y sigue sus pedidos."
        admin = person "Administrador" "Gestiona catalogo, pedidos, pagos por transferencia y solicitudes."
        proveedor = softwareSystem "Proveedor de pagos" "Pasarela externa (en pruebas: SandboxPay)." {
            tags "Externo"
        }

        tienda = softwareSystem "Tienda ChocoMania" "Tienda online de chocolates y reposteria." {
            tags "SistemaEvaluado"

            sitio = container "Sitio web" "Pantallas responsivas: catalogo, producto, carrito, cuenta, pedidos especiales." "PHP, HTML, CSS, JS" {
                tags "Frontend"
            }
            gateway = container "API Gateway" "Unico punto de entrada. Tabla de 22 rutas, sesion por cookie HttpOnly, roles, limites, timeouts, X-Request-ID." "Python, FastAPI"
            auth = container "Auth Service" "Login, registro, introspeccion y logout. PBKDF2 con sal." "Python, FastAPI"
            vault = container "Administrador de secretos" "Credenciales entre servicios y claves de la pasarela. Una ruta y un token de solo lectura por servicio; rotacion sin reinicio." "HashiCorp Vault" {
                tags "Secretos"
            }
            graphql = container "GraphQL Gateway" "Agrega orders + inventory + payments + clients. Privado." "Python, Strawberry"
            inventory = container "inventory" "Catalogo, imagenes, stock y reservas. Autoridad del precio." "Python, FastAPI"
            orders = container "orders" "Pedidos, detalle e historial de estados. Autoridad del estado del pedido." "Python, FastAPI"
            clients = container "clients" "Perfil, datos de contacto y solicitudes." "Python, FastAPI"
            payments = container "payments" "Inicio de pagos, avisos firmados, idempotencia." "Python, FastAPI"
            dbAuth = container "identity.db" "Usuarios y sesiones (hash del token)." "SQLite" {
                tags "BaseDatos"
            }
            dbInv = container "inventory.db" "Productos, tags, imagenes, reservas." "SQLite" {
                tags "BaseDatos"
            }
            dbOrd = container "orders.db" "Pedidos, items, eventos." "SQLite" {
                tags "BaseDatos"
            }
            dbCli = container "clients.db" "Clientes y solicitudes." "SQLite" {
                tags "BaseDatos"
            }
            dbPay = container "payments.db" "Pagos y avisos del proveedor." "SQLite" {
                tags "BaseDatos"
            }
        }

        visitante -> tienda "Consulta catalogo y pide cotizaciones"
        cliente -> tienda "Compra y sigue sus pedidos"
        admin -> tienda "Administra la tienda"
        tienda -> proveedor "Crea cobros y recibe avisos firmados"
        cliente -> proveedor "Paga en la pagina del proveedor"

        visitante -> tienda.gateway "Navega" "HTTPS"
        cliente -> tienda.gateway "Usa la tienda" "HTTPS, cookie HttpOnly"
        admin -> tienda.gateway "Administra" "HTTPS, cookie HttpOnly"
        tienda.gateway -> tienda.sitio "Sirve las paginas" "HTTP"
        tienda.gateway -> tienda.vault "Lee secret/gateway" "HTTP, token de solo lectura"
        tienda.auth -> tienda.vault "Lee secret/auth" "HTTP, token de solo lectura"
        tienda.inventory -> tienda.vault "Lee secret/inventory" "HTTP, token de solo lectura"
        tienda.orders -> tienda.vault "Lee secret/orders" "HTTP, token de solo lectura"
        tienda.clients -> tienda.vault "Lee secret/clients" "HTTP, token de solo lectura"
        tienda.payments -> tienda.vault "Lee secret/payments" "HTTP, token de solo lectura"
        tienda.graphql -> tienda.vault "Lee secret/graphql" "HTTP, token de solo lectura"
        tienda.gateway -> tienda.auth "Login e introspeccion" "HTTP, credencial gateway"
        tienda.gateway -> tienda.inventory "Catalogo y administracion" "REST, credencial gateway"
        tienda.gateway -> tienda.orders "Pedidos" "REST, credencial gateway + identidad"
        tienda.gateway -> tienda.clients "Perfil y solicitudes" "REST, credencial gateway + identidad"
        tienda.gateway -> tienda.payments "Pagos y avisos" "REST, credencial gateway"
        tienda.gateway -> tienda.graphql "Consultas agregadas" "GraphQL, credencial gateway + identidad"
        tienda.graphql -> tienda.orders "Pedidos" "REST, credencial graphql"
        tienda.graphql -> tienda.inventory "Productos por lote" "REST, credencial graphql"
        tienda.graphql -> tienda.payments "Pagos por lote" "REST, credencial graphql"
        tienda.graphql -> tienda.clients "Perfiles por lote" "REST, credencial graphql"
        tienda.orders -> tienda.inventory "Reserva, confirma y libera stock" "REST, credencial orders"
        tienda.payments -> tienda.orders "Lee monto y marca pagado" "REST, credencial payments"
        tienda.payments -> proveedor "Crea checkout" "HTTPS, API key"
        proveedor -> tienda.gateway "Aviso de pago" "HTTPS, firma HMAC"
        tienda.auth -> tienda.dbAuth "Lee y escribe"
        tienda.inventory -> tienda.dbInv "Lee y escribe"
        tienda.orders -> tienda.dbOrd "Lee y escribe"
        tienda.clients -> tienda.dbCli "Lee y escribe"
        tienda.payments -> tienda.dbPay "Lee y escribe"

        local = deploymentEnvironment "Local" {
            deploymentNode "Equipo del desarrollador" "" "Windows / Linux, Python 3.12+" {
                deploymentNode "Red publica" "" "localhost" {
                    containerInstance tienda.gateway
                    containerInstance tienda.sitio
                }
                deploymentNode "Red privada" "" "127.0.0.1, sin puertos hacia afuera en Docker" {
                    containerInstance tienda.auth
                    containerInstance tienda.vault
                    containerInstance tienda.graphql
                    containerInstance tienda.inventory
                    containerInstance tienda.orders
                    containerInstance tienda.clients
                    containerInstance tienda.payments
                }
                deploymentNode "Persistencia" "" "Archivos SQLite por servicio" {
                    containerInstance tienda.dbAuth
                    containerInstance tienda.dbInv
                    containerInstance tienda.dbOrd
                    containerInstance tienda.dbCli
                    containerInstance tienda.dbPay
                }
            }
        }
    }

    views {
        systemContext tienda "C1_Contexto" "C1 - Contexto de ChocoMania" {
            include *
            autoLayout lr
        }
        container tienda "C2_Contenedores" "C2 - Contenedores y almacenes de datos" {
            include *
            autoLayout lr
        }
        dynamic tienda "Compra" "Compra con pago por tarjeta" {
            cliente -> tienda.gateway "POST /api/orders"
            tienda.gateway -> tienda.auth "Introspeccion de la sesion"
            tienda.gateway -> tienda.orders "Crear pedido"
            tienda.orders -> tienda.inventory "Reservar stock y obtener precios"
            tienda.gateway -> tienda.payments "POST /api/payments"
            tienda.payments -> tienda.orders "Leer monto real"
            tienda.payments -> proveedor "Crear checkout"
            cliente -> proveedor "Aprueba el pago"
            proveedor -> tienda.gateway "Aviso firmado"
            tienda.gateway -> tienda.payments "Verificar firma y evento"
            tienda.payments -> tienda.orders "Marcar pagado"
            tienda.orders -> tienda.inventory "Confirmar reserva"
            autoLayout lr
        }
        dynamic tienda "MisPedidos" "Mis pedidos con GraphQL" {
            cliente -> tienda.gateway "POST /api/graphql"
            tienda.gateway -> tienda.graphql "Consulta + identidad verificada"
            tienda.graphql -> tienda.orders "Pedidos del usuario"
            tienda.graphql -> tienda.inventory "Productos (1 lote)"
            tienda.graphql -> tienda.payments "Pagos (1 lote)"
            autoLayout lr
        }
        deployment tienda "Local" "Despliegue" {
            include *
            autoLayout lr
        }
        styles {
            element "Person" {
                shape Person
                background #08427b
                color #ffffff
            }
            element "SistemaEvaluado" {
                background #173b5d
                color #ffffff
            }
            element "Externo" {
                background #999999
                color #ffffff
            }
            element "Container" {
                shape RoundedBox
                background #e3eef5
                color #173b5d
            }
            element "Frontend" {
                shape WebBrowser
            }
            element "BaseDatos" {
                shape Cylinder
                background #5eaf0f
                color #ffffff
            }
            element "Secretos" {
                shape Hexagon
                background #f2c94c
            }
        }
    }
}
