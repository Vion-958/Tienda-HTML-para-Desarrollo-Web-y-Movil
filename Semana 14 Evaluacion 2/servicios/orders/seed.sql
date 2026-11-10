-- Pedidos de ejemplo (datos ficticios). Los numeros parten en 1001.
BEGIN;
INSERT INTO pedidos (id, user_id, estado, entrega, direccion, comuna, metodo_pago, subtotal, costo_envio, total, pago_id) VALUES
  (1001, 'USR-001', 'pagado', 'retiro', '', '', 'tarjeta', 15800, 0, 15800, 'PAY-SEED-1001'),
  (1002, 'USR-003', 'pendiente_pago', 'delivery', 'Calle Falsa 123', 'Santiago', 'transferencia', 12600, 3000, 15600, NULL),
  (1003, 'USR-001', 'pendiente_pago', 'retiro', '', '', 'tarjeta', 10400, 0, 10400, NULL);
INSERT INTO pedido_items VALUES
  (1001, 'choco-1', 'Torta tres leches de chocolate', 15800, 1),
  (1002, 'choco-5', 'Brownie de chocolate 70%', 4200, 3),
  (1003, 'choco-7', ('Alfajores ba' || char(241) || 'ados en chocolate'), 5200, 2);
INSERT INTO pedido_eventos (pedido_id, estado_anterior, estado_nuevo, actor) VALUES
  (1001, NULL, 'pendiente_pago', 'USR-001'),
  (1001, 'pendiente_pago', 'pagado', 'payments'),
  (1002, NULL, 'pendiente_pago', 'USR-003'),
  (1003, NULL, 'pendiente_pago', 'USR-001');
COMMIT;
