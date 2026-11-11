# Resultados de la prueba de carga

- Fecha: 2026-11-09 14:45
- Entorno: Linux 6.18.44-fc-v310, Python 3.13.18, 2 CPU, 7.8 GB RAM
- Carga: 20 usuarios concurrentes, 20 s por escenario, todo en una maquina (localhost)
- Datos: catalogo de prueba de 15 productos, SQLite por servicio
- Tipo: medicion (no proyeccion)

| Escenario | Usuarios | Solicitudes | Throughput (req/s) | p50 ms | p95 ms | p99 ms | Errores | Objetivo p95 ms | Cumple |
|---|---|---|---|---|---|---|---|---|---|
| catalogo | 20 | 5767 | 287.4 | 62.0 | 121.2 | 163.9 | 0.0% | 500 | si |
| mis_pedidos_graphql | 20 | 1451 | 72.1 | 263.9 | 394.8 | 479.9 | 0.0% | 800 | si |
| crear_y_cancelar_pedido | 20 | 1066 | 52.6 | 365.0 | 543.0 | 726.4 | 0.0% | 1000 | si |

## CPU y memoria por proceso

| Proceso | CPU usada en la prueba (s) | Memoria RSS al final (MB) |
|---|---|---|
| vault | 0.01 | 19.6 |
| auth | 8.3 | 52.6 |
| inventory | 23.37 | 59.8 |
| clients | 0.07 | 48.2 |
| orders | 12.55 | 65.2 |
| payments | 3.08 | 57.6 |
| pasarela | 0.07 | 48.8 |
| graphql | 14.1 | 76.3 |
| gateway | 31.24 | 60.3 |
