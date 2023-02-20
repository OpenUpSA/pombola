# Based on https://github.com/appropriate/docker-postgis/blob/master/9.6-2.5/Dockerfile

FROM postgres:9.6

ENV POSTGIS_MAJOR 2.3

RUN echo "" | tee /etc/apt/sources.list.d/pgdg.list \
      && apt-get update \
      && apt-get install -y apt-transport-https \
      && echo "deb [ signed-by=/usr/local/share/keyrings/postgres.gpg.asc ] http://apt-archive.postgresql.org/pub/repos/apt/ stretch-pgdg main 9.6" | tee /etc/apt/sources.list.d/pgdg.list

RUN apt-get update \
      && apt-cache showpkg postgresql-$PG_MAJOR-postgis-$POSTGIS_MAJOR \
      && apt-get install -y --no-install-recommends \
           postgresql-$PG_MAJOR-postgis-$POSTGIS_MAJOR \
           postgresql-$PG_MAJOR-postgis-$POSTGIS_MAJOR-scripts \
      && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /docker-entrypoint-initdb.d
COPY ./initdb-postgis.sh /docker-entrypoint-initdb.d/postgis.sh
COPY ./initdb-test-database.sql /docker-entrypoint-initdb.d/initdb-test-database.sql
