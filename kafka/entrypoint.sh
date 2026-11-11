#!/usr/bin/env bash
# Точка входа sm-kafka:
#  1. Генерирует PKCS12 keystore и файлы с паролями в /etc/kafka/secrets
#     из PEM-сертификата (/etc/kafka/ssl), если их ещё нет.
#  2. Генерирует JAIS-конфиг /etc/kafka/jaas.conf из user-директив
#     /etc/kafka/auth.conf (SASL/PLAIN, один механизм для всех клиентов).
#  3. Запускает Apache Kafka (KRaft) в фоне.
#  4. Когда брокер поднялся, применяет topic/acl-директивы auth.conf.
#     Все операции идемпотентны — конфиг применяется при каждом старте.
set -uo pipefail

SSL_DIR=/etc/kafka/ssl
SECRETS_DIR=/etc/kafka/secrets
STORE_PASSWORD=changeit
CONF=/etc/kafka/auth.conf
JAAS=/etc/kafka/jaas.conf

mkdir -p "$SECRETS_DIR"
chmod 700 "$SECRETS_DIR" || true

if [ ! -f "$SECRETS_DIR/keystore.p12" ]; then
  openssl pkcs12 -export \
    -in "$SSL_DIR/server.crt" \
    -inkey "$SSL_DIR/server.key" \
    -out "$SECRETS_DIR/keystore.p12" \
    -name kafka \
    -passout "pass:${STORE_PASSWORD}"
fi

# Пароли читает configure-скрипт apache/kafka (KAFKA_SSL_*_CREDENTIALS)
printf '%s' "$STORE_PASSWORD" > "$SECRETS_DIR/keystore_creds"
printf '%s' "$STORE_PASSWORD" > "$SECRETS_DIR/key_creds"

# --- JAAS: PLAIN-пользователи из auth.conf ---
{
  echo 'KafkaServer {'
  echo '  org.apache.kafka.common.security.plain.PlainLoginModule required'
  echo '  username="unused"'
  echo '  password="unused"'
  echo '  user_unused="unused"'
  if [ -f "$CONF" ]; then
    grep -E '^[[:space:]]*user[[:space:]]' "$CONF" | while read -r _ username userpass _; do
      printf '  user_%s="%s"\n' "$username" "$userpass"
    done
  fi
  echo '  end_marker="ok";' # ';' в конце списка опций обязателен для JAAS
  echo '};'
} > "$JAAS"
chmod 600 "$JAAS" || true

# --- Kafka ---
/etc/kafka/docker/run "$@" &
KAFKA_PID=$!

BOOTSTRAP=127.0.0.1:9092 # PLAINTEXT, только localhost внутри контейнера, без авторизации

ready=0
for _ in $(seq 1 90); do
  if /opt/kafka/bin/kafka-broker-api-versions.sh --bootstrap-server "$BOOTSTRAP" >/dev/null 2>&1; then
    ready=1
    break
  fi
  sleep 2
done

if [ "$ready" != 1 ]; then
  echo "sm-kafka: брокер не поднялся за 180s, применение auth.conf пропущено" >&2
elif [ ! -f "$CONF" ]; then
  echo "sm-kafka: $CONF не найден — скопируйте kafka/auth.conf.example в kafka/auth.conf" >&2
else
  echo "sm-kafka: применяю $CONF (topic/acl; user уже в jaas.conf)"
  while read -r directive f1 f2 f3 f4; do
    case "$directive" in
      user)
        ;; # уже учтён при генерации jaas.conf
      topic)
        # topic <name> <partitions>
        /opt/kafka/bin/kafka-topics.sh --bootstrap-server "$BOOTSTRAP" \
          --create --if-not-exists --topic "$f1" --partitions "$f2" --replication-factor 1 \
          && echo "  topic $f1" \
          || echo "  ! ошибка topic $f1" >&2
        ;;
      acl)
        # acl <principal> <topic|group|cluster> <name|-> <ops через запятую>
        case "$f2" in
          topic)   res=(--topic "$f3") ;;
          group)   res=(--group "$f3") ;;
          cluster) res=(--cluster) ;;
          *) echo "  ! неизвестный тип ресурса: $f2" >&2; continue ;;
        esac
        IFS=',' read -ra ops <<< "$f4"
        for op in "${ops[@]}"; do
          /opt/kafka/bin/kafka-acls.sh --bootstrap-server "$BOOTSTRAP" \
            --add --allow-principal "$f1" --allow-host '*' "${res[@]}" --operation "$op" \
            && echo "  acl $f1 $f2 $f3 $op" \
            || echo "  ! ошибка acl $f1 $f2 $f3 $op" >&2
        done
        ;;
      *)
        echo "  ! неизвестная директива: $directive" >&2 ;;
    esac
  done < <(grep -vE '^[[:space:]]*(#|$)' "$CONF")
fi

wait "$KAFKA_PID"
