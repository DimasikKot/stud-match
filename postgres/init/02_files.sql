-- Файл можно перезапустить на живой БД (postgres/reinit.sh): он удаляет свои таблицы
-- и создаёт их заново. CASCADE снимает внешние ключи зависимых таблиц — reinit.sh
-- перезапустит и файлы, где они объявлены.

DROP TABLE IF EXISTS files CASCADE;

CREATE TABLE files (
  id         SERIAL        PRIMARY KEY,
  name       VARCHAR (255) NOT NULL,
  object_key VARCHAR (255) NOT NULL,
  path       VARCHAR (255) NOT NULL,
  size       INT           NOT NULL,
  created_at TIMESTAMP     DEFAULT CURRENT_TIMESTAMP NOT NULL,
  updated_at TIMESTAMP     DEFAULT CURRENT_TIMESTAMP NOT NULL
);
