#!/usr/bin/env bash
# Точечная переинициализация БД без пересоздания postgres/data.
# Перезапускает указанные файлы postgres/init и все файлы, чьи таблицы ссылаются
# (REFERENCES) на таблицы перезапускаемых — их внешние ключи снимает DROP ... CASCADE.
#
#   postgres/reinit.sh plan <file>...                какие файлы будут перезапущены
#   postgres/reinit.sh apply <backup-id> <file>...   pg_dump + перезапуск одной транзакцией
#   postgres/reinit.sh restore <backup-id>           вернуть БД из бэкапа, сделанного apply
#
# Бэкап: /var/lib/postgresql/pre_reinit_<backup-id>.dump в контейнере (./postgres/data на хосте).
set -euo pipefail
export LC_ALL=C

CONTAINER="${PG_CONTAINER:-sm-postgres}"
INIT_DIR="$(cd "$(dirname "$0")" && pwd)/init"
BACKUP_DIR=/var/lib/postgresql

tables_of() { grep -oiE 'CREATE TABLE +(IF NOT EXISTS +)?[a-z_][a-z0-9_]*' "$1" | awk '{print tolower($NF)}' || true; }
refs_of() { grep -oiE 'REFERENCES +[a-z_][a-z0-9_]*' "$1" | awk '{print tolower($NF)}' || true; }

plan() {
  local -A selected=()
  local f r dropped added=1
  for f in "$@"; do
    f="$INIT_DIR/$(basename "$f")"
    if [[ $f == *.sql && -f $f ]]; then selected[$f]=1; fi
  done
  while ((added)); do
    added=0
    dropped=" $(for f in "${!selected[@]}"; do tables_of "$f"; done | tr '\n' ' ')"
    for f in "$INIT_DIR"/*.sql; do
      [[ -n ${selected[$f]:-} ]] && continue
      for r in $(refs_of "$f"); do
        if [[ $dropped == *" $r "* ]]; then
          selected[$f]=1
          added=1
          break
        fi
      done
    done
  done
  for f in "$INIT_DIR"/*.sql; do
    if [[ -n ${selected[$f]:-} ]]; then echo "$f"; fi
  done
}

# Ждём, пока Postgres начнёт слушать TCP: во время первичной инициализации
# (docker-entrypoint-initdb.d) он доступен только через сокет.
wait_ready() {
  local i
  for i in $(seq 1 60); do
    docker exec "$CONTAINER" pg_isready -q -h 127.0.0.1 && return 0
    sleep 2
  done
  echo "::error::$CONTAINER is not ready" >&2
  return 1
}

apply() {
  local id=$1 files f
  shift
  mapfile -t files < <(plan "$@")
  if ((${#files[@]} == 0)); then
    echo "=== [postgres] No init files to re-run ==="
    return 0
  fi
  echo "=== [postgres] Re-run: ${files[*]##*/} ==="
  wait_ready
  docker exec "$CONTAINER" sh -c \
    'rm -f "$1"/pre_reinit_*.dump && pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc -f "$1/pre_reinit_$2.dump"' \
    sh "$BACKUP_DIR" "$id"
  echo "Backup created: $BACKUP_DIR/pre_reinit_$id.dump"
  for f in "${files[@]}"; do
    cat "$f"
    echo
  done | docker exec -i "$CONTAINER" sh -c \
    'psql -X -q -v ON_ERROR_STOP=1 --single-transaction -U "$POSTGRES_USER" -d "$POSTGRES_DB" >/dev/null'
}

restore() {
  local id=$1
  wait_ready
  docker exec "$CONTAINER" sh -c '
    f="$1/pre_reinit_$2.dump"
    if [ ! -f "$f" ]; then
      echo "::warning::$f not found — apply did not run in this deploy, DB left intact"
      exit 0
    fi
    # Схему пересоздаём целиком: в БД могут быть новые таблицы, которых нет в бэкапе
    { echo "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"; pg_restore -f - "$f"; } |
      psql -X -q -v ON_ERROR_STOP=1 --single-transaction -U "$POSTGRES_USER" -d "$POSTGRES_DB" >/dev/null &&
      rm -f "$f" &&
      echo "=== [postgres] Restored from $f ==="' sh "$BACKUP_DIR" "$id"
}

case "${1:-}" in
  plan) shift && plan "$@" ;;
  apply) shift && apply "$@" ;;
  restore) shift && restore "$@" ;;
  *)
    sed -n '2,10p' "$0" >&2
    exit 2
    ;;
esac
