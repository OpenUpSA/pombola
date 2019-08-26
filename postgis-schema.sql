-- https://www.postgis.net/2017/11/07/tip-move-postgis-schema/

UPDATE pg_extension
  SET extrelocatable = TRUE
    WHERE extname = 'postgis';

CREATE SCHEMA postgis;

ALTER DATABASE pombola
SET search_path = public,postgis;

ALTER EXTENSION postgis
  SET SCHEMA postgis;
