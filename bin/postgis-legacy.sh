#!/bin/sh

set -e

# Perform all actions as $POSTGRES_USER
export PGUSER="$POSTGRES_USER"

psql -f /usr/share/postgresql/9.6/contrib/postgis-2.5/legacy_minimal.sql
