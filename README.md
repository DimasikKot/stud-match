## Действия перед запуском

### Настройте `git`

1. Установите `vscode`
2. Установите `git`

https://git-scm.com/

3. Зайти в `GitHub` в `vscode`

4. Привязать почту к коммитам (обязательно)

```bash
git config --global user.email ЭЛЕКТРОННАЯ-ПОЧТА
```

5. Установить отображаемое при коммите имя (обязательно)

```bash
git config --global user.name ФАМИЛИЯ-ИМЯ
```

6. Скопируйте репозиторий с `GitHub`'а

```bash
git clone https://github.com/DimasikKot/stud-match.git

```

7. Установите хук:

```bash
pip install pre-commit
pre-commit install

```

### Настройте `Docker`

1. Установите `docker`

2. Выдайте `docker`'у права супер-пользователя, чтобы не вводить постоянно `sudo` (если на `Linux`)

```bash
sudo usermod -aG docker $USER
```

3. Создайте общие сети

```bash
docker network create nginx-network

```

### Настройте `PostgreSQL`

2. Установите `pgAdmin 4`

3. Подключитесь к БД по `localhost:5432`

4. Активируйте скрипт `init.sql`

### Задание своих переменных среды

1. Заполните `.env` по примеру `.env.example`

## Запуск проекта

```bash
docker compose up --build

```

> Чтобы освободить консоль нажмите `D`

> или при запуске добавьте флаг `-d`

## URLs

### frontend

https://localhost/

### backend

https://localhost/backend/docs

## Скрыть лишние папки в `vscode`

1. Откройте настройки (`File` > `Preferences` > `Settings` ИЛИ `F1` > `>Preferences: Open Settings (UI)`);
2. Поищите `exclude` в строке поиска по настройкам ИЛИ `Files` > `Exclude`;
3. Нажмите кнопку `Add Pattern` и добавьте `**/__pycache__` паттерн;
4. По желанию добавьте `**/node_modules` паттерн для `frontend`'a;
5. По желанию добавьте `.venv` паттерн для виртуальной среды `python`'a;

## Включение подсветки синтаксиса в `vscode`

### `extensions`

Во вкладке дополнений в `vscode` напишите текст ниже и установите все дополнения

```bash
@recommended
```

### `backend` / `ml`

1. Установите `Python` (советую 3.13)

2. Загрузите библиотеки из `requirements.txt`

```bash
pip install --no-cache-dir -r requirements.txt

```

> Эта же команда используется для добавления и обновления уже установленных библиотек

### `frontend`

1. Установите `node.js`

2. Активируйте переменные среды (если на `Windows`)

Вводить в `PowerShell`

```bash
Set-ExecutionPolicy RemoteSigned

```

3. Загрузите библиотеки из `package.json`

```bash
npm install

```

> Эта же команда используется для добавления и обновления уже установленных библиотек

> Перед перезагрузкой контейнеров после установки зависимостей ВСЕГДА УДАЛЯЙТЕ СТАРЫЙ `volumes` в `docker`'е

### Установка новых библиотек:

1. Установить нужные библиотеки:

```bash
npm install НАЗВАНИЕ
```

2. Обновить зависимости:

```bash
npm audit fix

```

3. Остановить все контейнеры:

```bash
docker-compose down

```

4. Удалить volumes:

```bash
docker volume prune -a

```

5. Перезапустить контейнеры:

```bash
docker-compose up --build

```

### Увеличить память контейнера (по желанию):

```bash
docker update --memory 4g ml

```

### Применить свой HUGGINGFACE_TOKEN в контейнере воркера (по желанию):

```bash
docker exec -it ml bash
```

```bash
hf auth login --token hf_xxxxx
```

### Очистка докера от ненужного хлама из прошлого

1. Базовая очистки лишнего (но она ничего не сделала)

```bash
docker system prune -a
```

2. Полная очистка (работающие не удалятся)

```bash
docker system prune -a --volumes
```

### Проверить работает ли SSL соединение к БД

```sql
SELECT
  a.datname,
  a.usename,
  a.client_addr,
  s.ssl,
  s.version,
  s.cipher
FROM
  pg_stat_activity a
LEFT JOIN
  pg_stat_ssl s ON a.pid = s.pid
WHERE
  a.state = 'active';
```

### Запуск определённого docker-compose файла

```bash
docker compose -f localhost.docker-compose.yaml up -d
```

### Правильное использование async функций во фронтенде

```ts
fetchBackendHealth().then((v) => v !== undefined && setBackendStatus(v));
fetchPostgresHealth().then((v) => v !== undefined && setPostgresStatus(v));
fetchRedisHealth().then((v) => v !== undefined && setRedisStatus(v));
```

## Kafka: SASL_SSL + PLAIN, декларативный provisioning

Kafka работает в KRaft-режиме с авторизацией: внешний доступ — `SASL_SSL` (порт `KAFKA_SSL_PORT`, внутри контейнера `8092`), клиенты внутри docker-сети — `SASL_PLAINTEXT_INTERNAL` (`sm-kafka:8292`, SASL без TLS). `PLAINTEXT` слушает только `127.0.0.1` внутри контейнера — используется для healthcheck и provisioning, наружу не публикуется.

**Пользователи, топики и права настраиваются в `kafka/auth.conf`** — ничего создавать вручную не нужно: при каждом старте `sm-kafka` entrypoint-скрипт генерирует JAAS с PLAIN-пользователями, дожидается готовности брокера и применяет топики и ACL. Все операции идемпотентны.

### Запуск

1. Скопируйте шаблон и заполните своими значениями:

```bash
cp kafka/auth.conf.example kafka/auth.conf
```

В `auth.conf` директивы `user` / `topic` / `acl` — см. комментарии в файле. По умолчанию там 1 backend + 3 llm-worker'а (`llm_worker_1..3`).

2. Заполните `.env` (см. `.env.example`): адрес брокера — `KAFKA_HOST`, `KAFKA_PORT`, `KAFKA_ADVERTISED_HOST`, `KAFKA_SSL_PORT`; креды клиентов — `KF_USERNAME`/`KF_PASSWORD` у backend и `LLM_KF_USERNAME`/`LLM_KF_PASSWORD` у каждого воркера (пароли должны совпадать с `user` в `auth.conf`).

3. Поднимите Kafka:

```bash
docker compose -f rpi5.docker-compose.yaml up -d sm-kafka
```

После правок `auth.conf` примените изменения:

```bash
docker compose -f rpi5.docker-compose.yaml restart sm-kafka
```

### llm-worker на другой машине

В `.env` на машине воркера укажите публичный адрес Kafka и креды своего пользователя `llm_worker_N` из `auth.conf` (у каждого воркера свой логин/пароль):

```env
KAFKA_HOST="stud-match.mooo.com"   # публичный хост Kafka
KAFKA_PORT=8092                    # KAFKA_SSL_PORT на сервере
LLM_KF_USERNAME="llm_worker_1"     # llm_worker_1 / _2 / _3 — по одному на воркер
LLM_KF_PASSWORD="CHANGE_ME"
```

```bash
docker compose -f gtx1650ti.docker-compose.yaml up -d --build
```

### ACL и несколько backend

- Доступ к топикам/группам ограничен ACL из `auth.conf`: backend (`User:backend`) пишет в `llm.tasks` и читает `llm.results`, каждый `llm_worker_N` читает `llm.tasks` и пишет `llm.results`. Все воркеры делят общую consumer group `sm-llm-worker` — задача достаётся только одному воркеру.
- Права действуют только на ресурсы, для которых есть ACL; остальные доступны любому авторизованному пользователю (`KAFKA_ALLOW_EVERYONE_IF_NO_ACL_FOUND=true`).
- Все backend могут использовать одни топики `llm.tasks`/`llm.results`, но у каждого должен быть свой `KAFKA_RESULTS_GROUP_ID` и свой `Read,Describe` ACL на эту group в `auth.conf`, иначе consumer group будет делить сообщения `llm.results` между backend'ами.

### Сетевая безопасность

SASL_SSL защищает аутентификацию и шифрует трафик, но порт Kafka всё равно не стоит открывать всему интернету. Ограничьте `KAFKA_SSL_PORT` firewall'ом по IP воркеров или выведите воркеров в VPN/Tailscale/WireGuard.
