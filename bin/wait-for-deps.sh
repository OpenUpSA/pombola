#!/bin/sh

postgres_ready() {
python << END
import sys
import psycopg2
try:
    psycopg2.connect("$DATABASE_URL")
except psycopg2.OperationalError as e:
    print(e)
    sys.exit(-1)
sys.exit(0)
END
}

elasticsearch_ready() {
python << EOF
import socket
from contextlib import closing
import os

(host, port_str) = os.environ["ELASTICSEARCH_URL"].split(":")
with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
    sock.settimeout(2)
    if sock.connect_ex((host, int(port_str))) == 0:
        exit(0)
    else:
        exit(1)
EOF
}

until postgres_ready; do
  >&2 echo 'Waiting for PostgreSQL to become available...'
  sleep 1
done
>&2 echo 'PostgreSQL is available'

until elasticsearch_ready; do
  >&2 echo "elasticsearch is unavailable - sleeping"
  sleep 1
done

exec "$@"
