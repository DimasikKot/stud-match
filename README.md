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

1. Создайте `.env.local` файлы в папках сервисов `backend` и `frontend`

2. Заполните `.env.local` по примерам `.env.example`

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
