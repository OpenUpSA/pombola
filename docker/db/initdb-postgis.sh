#!/bin/sh

set -e

# Perform all actions as $POSTGRES_USER
export PGUSER="$POSTGRES_USER"

echo "Loading PostGIS extensions into $POSTGRES_DB"
"${psql[@]}" --dbname="$POSTGRES_DB" <<-'EOSQL'
    CREATE SCHEMA postgis;
    CREATE EXTENSION postgis;
    UPDATE pg_extension SET extrelocatable = TRUE WHERE extname = 'postgis';
    CREATE EXTENSION postgis_topology;
    ALTER DATABASE pombola SET search_path = public,postgis,topology;
    GRANT ALL ON SCHEMA postgis TO public;
    ALTER EXTENSION postgis SET SCHEMA postgis;
EOSQL

psql "$POSTGRES_DB" < /usr/share/postgresql/9.6/contrib/postgis-2.3/legacy_minimal.sql
