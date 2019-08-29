#!/bin/sh

set -e

# Perform all actions as $POSTGRES_USER
export PGUSER="$POSTGRES_USER"

echo "Loading PostGIS extensions into $POSTGRES_DB"
"${psql[@]}" --dbname="$POSTGRES_DB" <<-'EOSQL'
    CREATE EXTENSION postgis;
    CREATE EXTENSION postgis_topology;
EOSQL

psql "$POSTGRES_DB" < /usr/share/postgresql/9.6/contrib/postgis-2.3/legacy_minimal.sql
