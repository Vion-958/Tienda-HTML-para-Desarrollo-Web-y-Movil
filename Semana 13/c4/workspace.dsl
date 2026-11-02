/*
 * ChocoManía - Modelo C4 (Structurizr DSL)
 *
 * Representa lo que realmente está construido en el repositorio:
 *   Semana 7   API GraphQL (Fastify + MongoDB)
 *   Semana 8-9 Sitio PHP, API Gateway, Auth Service, Vault y Backend
 *   Semana 13  Broker ActiveMQ con productor y consumidor STOMP
 *
 * Abrir en https://playground.structurizr.com (pegar este archivo) o con
 * Structurizr Lite:
 *   docker run -it --rm -p 8080:8080 -v "%cd%:/usr/local/structurizr" structurizr/lite
 */
workspace "ChocoManía" "Arquitectura de la tienda online ChocoManía (Desarrollo Web y Móvil)" {

    !identifiers hierarchical

    model {
        // ---------- Actores ----------
        visitante = person "Visitante" "Persona que mira la tienda sin iniciar sesión."
        cliente = person "Cliente" "Usuario con rol user (ej. ana). Consulta el catálogo y revisa sus pedidos."
        administrador = person "Administrador" "Usuario con rol admin (ej. ernesto). Administra el catálogo."

        // ---------- Sistema ----------
        tienda = softwareSystem "Tienda ChocoManía" "Tienda online de chocolates: catálogo, carrito, cuenta y pedidos." {
            tags "SistemaEvaluado"

            frontend = container "Sitio web" "Páginas de la tienda: inicio, catálogo, producto, carrito, empresa y Mi cuenta. No decide permisos ni guarda el token." "PHP 8.3, HTML, CSS, JavaScript" {
                tags "Frontend"
            }

            gateway = container "API Gateway" "Único punto de entrada (:8000). Sirve el sitio, valida la sesión, autoriza por rol y enruta /auth y /api." "Python, FastAPI, httpx"

            auth = container "Auth Service" "Verifica credenciales (PBKDF2), emite tokens opacos, introspección y logout (:8100)." "Python, FastAPI"

            identidades = container "Usuarios y sesiones" "Usuarios con hash y sal, y sesiones activas con vencimiento." "En memoria del Auth Service" {
                tags "BaseDatos"
            }

            vault = container "Administrador de secretos" "Guarda los secretos entre servicios y solo los entrega al Gateway (:8200)." "HashiCorp Vault (modo dev)" {
                tags "Secretos"
            }

            backend = container "Backend API" "Lógica de negocio: catálogo, alta de productos con imágenes, pedidos por usuario y su cancelación. Exige el secreto del Gateway (:9000)." "Python, FastAPI"

            catalogo = container "Catálogo, imágenes y pedidos" "Productos con tags y stock, imágenes subidas por el admin y pedidos de cada usuario." "En memoria del Backend" {
                tags "BaseDatos"
            }

            graphql = container "API GraphQL" "CRUD de productos con queries y mutations (:4000). Práctica de la Semana 7, todavía fuera del flujo del Gateway." "Node.js, Fastify, mercurius" {
                tags "Practica"
            }

            mongo = container "Base de productos" "Colección productos de la base chocomania." "MongoDB" {
                tags "BaseDatos" "Practica"
            }

            broker = container "Broker de mensajería" "Recibe y encola los pedidos en /queue/chocomania.pedidos hasta que alguien los consuma (:61613)." "Apache ActiveMQ Classic, STOMP 1.2" {
                tags "Cola"
            }

            productor = container "Productor de pedidos" "Serializa un pedido en texto, ancho fijo, XML o JSON y lo publica en la cola." "Python, stomp.py" {
                tags "Mensajeria"
            }

            consumidor = container "Procesador de pedidos" "Escucha la cola, interpreta cada formato, valida el pedido y confirma con ACK o rechaza con NACK." "Python, stomp.py" {
                tags "Mensajeria"
            }
        }

        // ---------- C1: actores con el sistema ----------
        visitante -> tienda "Mira productos publicados"
        cliente -> tienda "Consulta productos y revisa sus pedidos"
        administrador -> tienda "Administra el catálogo"

        // ---------- C2: actores con el sitio ----------
        visitante -> tienda.frontend "Navega el catálogo de respaldo" "Navegador web"
        cliente -> tienda.frontend "Inicia sesión, compra, ve y cancela sus pedidos" "Navegador web"
        administrador -> tienda.frontend "Inicia sesión, agrega y elimina productos" "Navegador web"

        // ---------- C2: entrada al backend ----------
        tienda.frontend -> tienda.gateway "Envía login y llamadas /api con la cookie de sesión" "HTTP, JSON, cookie HttpOnly"
        tienda.gateway -> tienda.frontend "Reenvía las páginas del sitio" "HTTP"

        // ---------- C2: seguridad y secretos ----------
        tienda.gateway -> tienda.vault "Lee los secretos internos" "HTTP, token de Vault"
        tienda.gateway -> tienda.auth "Hace login, introspección y logout" "HTTP, JSON, X-Introspection-Secret"
        tienda.auth -> tienda.identidades "Consulta usuarios y crea o revoca sesiones" "Acceso en memoria"

        // ---------- C2: enrutamiento al servicio de negocio ----------
        tienda.gateway -> tienda.backend "Enruta catálogo y pedidos con la identidad del usuario" "HTTP, JSON, X-Gateway-Secret"
        tienda.backend -> tienda.catalogo "Lee y escribe productos y pedidos" "Acceso en memoria"

        // ---------- C2: agregación GraphQL (Semana 7) ----------
        administrador -> tienda.graphql "Prueba queries y mutations en GraphiQL" "HTTP, GraphQL"
        tienda.graphql -> tienda.mongo "Lee y escribe productos" "MongoDB driver"

        // ---------- C2: mensajería asíncrona (Semana 13) ----------
        tienda.productor -> tienda.broker "Publica pedidos (texto, fijo, XML o JSON)" "STOMP SEND, persistente"
        tienda.broker -> tienda.consumidor "Entrega pedidos de a uno" "STOMP MESSAGE, ack client-individual"
        tienda.consumidor -> tienda.broker "Confirma (ACK) o rechaza (NACK) cada pedido" "STOMP ACK/NACK"
    }

    views {
        systemContext tienda "C1_Contexto" "C1 - Contexto de la tienda ChocoManía" {
            include *
            autoLayout lr
        }

        container tienda "C2_Contenedores" "C2 - Contenedores y almacenes de datos de ChocoManía" {
            include *
            autoLayout lr
        }

        container tienda "C2_Catalogo" "Vista focalizada: recorrido de una consulta del catálogo" {
            include visitante cliente tienda.frontend tienda.gateway tienda.vault tienda.auth tienda.identidades tienda.backend tienda.catalogo
            autoLayout lr
        }

        container tienda "C2_Administracion" "Vista focalizada: el administrador agrega o elimina un producto" {
            include administrador tienda.frontend tienda.gateway tienda.auth tienda.backend tienda.catalogo
            autoLayout lr
        }

        container tienda "C2_Mensajeria" "Vista focalizada: integración asíncrona con el broker" {
            include tienda.productor tienda.broker tienda.consumidor
            autoLayout lr
        }

        dynamic tienda "Dinamica_Login" "Cliente inicia sesión y ve sus pedidos" {
            cliente -> tienda.frontend "Escribe usuario y contraseña en Mi cuenta"
            tienda.frontend -> tienda.gateway "POST /auth/login"
            tienda.gateway -> tienda.vault "Obtiene el secreto de introspección"
            tienda.gateway -> tienda.auth "POST /login"
            tienda.auth -> tienda.identidades "Verifica el hash y crea la sesión"
            tienda.frontend -> tienda.gateway "GET /api/orders con la cookie"
            tienda.gateway -> tienda.auth "POST /introspect: ¿sesión activa?"
            tienda.gateway -> tienda.backend "GET /orders con la identidad del usuario"
            tienda.backend -> tienda.catalogo "Filtra los pedidos del usuario"
            autoLayout lr
        }

        dynamic tienda "Dinamica_Pedido_Asincrono" "Un pedido viaja por el broker" {
            tienda.productor -> tienda.broker "SEND a /queue/chocomania.pedidos"
            tienda.broker -> tienda.consumidor "MESSAGE con x-formato y content-type"
            tienda.consumidor -> tienda.broker "ACK si es válido, NACK si no cumple el contrato"
            autoLayout lr
        }

        styles {
            element "Person" {
                shape Person
                background #08427b
                color #ffffff
            }
            element "Software System" {
                shape RoundedBox
                background #1168bd
                color #ffffff
            }
            element "SistemaEvaluado" {
                background #173b5d
                color #ffffff
            }
            element "Container" {
                shape RoundedBox
                background #e3eef5
                color #173b5d
                stroke #173b5d
            }
            element "Frontend" {
                shape WebBrowser
                background #cde5f7
                color #153e5b
            }
            element "BaseDatos" {
                shape Cylinder
                background #5eaf0f
                color #ffffff
            }
            element "Secretos" {
                shape Hexagon
                background #f2c94c
                color #3d2c00
            }
            element "Cola" {
                shape Pipe
                background #8e5a2b
                color #ffffff
            }
            element "Mensajeria" {
                background #f3e3d3
                color #5a3311
            }
            element "Practica" {
                border Dashed
                opacity 70
            }
            relationship "Relationship" {
                color #52697e
                thickness 2
            }
        }
    }
}
