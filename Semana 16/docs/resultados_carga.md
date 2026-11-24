# Resultados de la prueba de carga

- Fecha: 2026-11-16 09:26
- Entorno: Linux 6.18.44-fc-v470, Python 3.13.18, 2 CPU, 7.8 GB RAM
- Carga: 20 usuarios concurrentes, 20 s por escenario, todo en una maquina (localhost)
- Datos: catalogo de prueba de 15 productos, SQLite por servicio
- Tipo: medicion (no proyeccion)

| Escenario | Usuarios | Solicitudes | Throughput (req/s) | p50 ms | p95 ms | p99 ms | Errores | Objetivo p95 ms | Cumple |
|---|---|---|---|---|---|---|---|---|---|
| catalogo | 20 | 6258 | 312.1 | 56.8 | 118.1 | 166.1 | 0.0% | 500 | si |
| mis_pedidos_graphql | 20 | 1585 | 78.8 | 238.5 | 404.9 | 513.8 | 0.0% | 800 | si |
| crear_y_cancelar_pedido | 20 | 1221 | 60.5 | 306.4 | 516.0 | 692.9 | 0.0% | 1000 | si |

## CPU y memoria por proceso

| Proceso | CPU usada en la prueba (s) | Memoria RSS al final (MB) |
|---|---|---|
| vault | 0.01 | 19.6 |
| auth | 8.28 | 62.8 |
| inventory | 23.28 | 68.2 |
| clients | 0.06 | 55.5 |
| orders | 12.33 | 70.1 |
| payments | 2.96 | 60.5 |
| pasarela | 0.06 | 48.7 |
| graphql | 14.22 | 79.1 |
| gateway | 32.33 | 62.7 |
