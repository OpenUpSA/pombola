# Install

Pombola is mostly a standard Django project.

We use docker to make development, test and production as similar as possible.

In development, we use docker-compose.

In production, we use dokku. Dokku manages environment variables for
configuration and secrets, and proxies requests to the container IP.

If you'd like to run this in another way, use the docker-compose.yml file as the
entrypoint to understand the environment and dependencies of this app.

## Where to put the code and data

In addition to the downloaded code several other directories are needed for
dynamic data such as the search indexes, uploaded images, various caches etc.

These extra directories are by default put inside the `data/` directory, although
this can be modified using the `DATA_DIR` configuration variable.

Development
-----------

The code is available via github: https://github.com/OpenUpSA/pombola

```
git clone https://github.com/OpenUpSA/pombola.git
```

Start the app, DB and search index:

```
docker-compose up
```

Load the schema and data:

```
zcat pg-dump_schema.sql.gz | docker-compose run --rm db psql postgres://pombola:pombola@db/pombola
zcat pg-dump_data.sql.gz | docker-compose run --rm db psql postgres://pombola:pombola@db/pombola
```

Build the search index:

```
docker-compose run --rm app python manage.py rebuild_index
```

Now you can visit the site at [http://localhost:8000](http://localhost:8000)

-----

Delete the DB, media files and search index to start afresh:

```
docker-compose down --volumes
```

Production deployment
---------------------

### Elasticsearch

[Deploy Elasticsearch 0.90.13](https://github.com/OpenUpSA/elasticsearch-0.90)

### Postgres

Deploy Postgres with PostGIS

```
export POSTGRES_IMAGE="openup/postgres-9.6-postgis-9.3"
export POSTGRES_IMAGE_VERSION="latest"
dokku postgres:create pombola
dokku postgres:link pombola pombola
```

`dokku postgres:connect pombola`

```
create extension postgis;
```

`dokku postgres:enter pombola bash`

```
psql -U postgres -f /usr/share/postgresql/9.6/contrib/postgis-2.3/legacy_minimal.sql pombola
```

`dokku postgres:connect pombola`

```
CREATE EXTENSION postgis;
CREATE EXTENSION postgis_topology;
```

### Create and configure the app

```
dokku apps:create pombola
dokku config:set pombola \
    EMAIL_HOST=smtp.sendgrid.net \
    EMAIL_HOST_USER=apikey \
    EMAIL_HOST_PASSWORD=... \
    EMAIL_PORT=587 \
    POMBOLA_DATADIR=/data \
    DEFAULT_FROM_EMAIL=contact@pa.org.za \
    MANAGERS_EMAIL=contact@pa.org.za \
    ERRORS_EMAIL=webapps@openup.org.za \
    DJANGO_SECRET_KEY=... \
    TWITTER_USERNAME=PeoplesAssem_SA \
    ELASTICSEARCH_URL=elasticsearch.example.com:9200 \
    DATABASE_URL=postgres://pombola:...@db.example.com/pombola \
    GOOGLE_ANALYTICS_ACCOUNT=UA-47810266-1 \
    DISQUS_SHORTNAME=peoplesassembly.disqus.com \
    PMG_COMMITTEE_USER=... \
    PMG_COMMITTEE_PASSWORD=... \
    PMG_API_KEY=... \
    POPIT_API_URL=True \
    GOOGLE_MAPS_GEOCODING_API_KEY=...

dokku docker-options:add pombola deploy "-v /var/pombola-data:/data"
dokku docker-options:add pombola run "-v /var/pombola-data:/data"
```

```
git remote add dokku dokku@pa.openup.org.za:pombola
```

```
git push dokku master
```

Configure NGINX to serve the static and media files

Edit `/home/dokku/pombola/nginx.conf.d/media.conf` to look like this:

```
location /static {
    alias /var/pombola-data/collected_static;
}


location /media_root {
    alias /var/pombola-data/media_root;
}
```

Test the config with `sudo nginx -t`

Reload nginx: `sudo systemctl restart nginx`

### Cron jobs

TBC