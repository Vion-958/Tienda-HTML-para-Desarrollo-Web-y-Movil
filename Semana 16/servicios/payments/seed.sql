-- Pagos de los pedidos de ejemplo (datos ficticios)
INSERT INTO pagos (id, pedido_id, user_id, monto, metodo, estado, checkout_id, sincronizado) VALUES
  ('PAY-SEED-1001', 1001, 'USR-001', 15800, 'tarjeta', 'aprobado', 'chk_seed_1001', 1),
  ('PAY-SEED-1002', 1002, 'USR-003', 15600, 'transferencia', 'pendiente', NULL, 0);
