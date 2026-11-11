-- Usuarios ficticios: ana / 1234 (user), ernesto / admin123 (user, admin)
INSERT INTO usuarios (user_id, username, sal, hash, iteraciones, roles) VALUES
  ('USR-001', 'ana', 'e1b65c41c612b147f7b65fe414df9316', 'b45d302e407ad7be8b4bc5a4a8cb8cd8e1354061e97d8d745bd6bc088afef4af', 200000, 'user'),
  ('USR-003', 'ernesto', 'ffc269d40f83c7dd11ee1ba3e9ec5c33', '33396ddea07ea52dd0f524228f367ad204a22c287071238df53d6d285b46983f', 200000, 'user,admin');
