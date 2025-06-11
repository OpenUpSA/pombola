FROM python:3.9.22-bookworm

ENV PYTHONUNBUFFERED 1
ENV COUNTRY_APP=south_africa

RUN echo "deb http://deb.debian.org/debian bullseye main" > /etc/apt/sources.list.d/bullseye.list && \
    apt-get update && \
    apt-get install -y \
        ruby2.7-dev \
        antiword \
        binutils \
        libffi-dev \
        libjpeg-dev \
        libpq-dev \
        libxml2-dev \
        libxslt1-dev \
        libproj-dev \
        gdal-bin \
        libgdal-dev \
        poppler-utils \
        yui-compressor \
        zlib1g-dev \
        postgresql-client \
        awscli \
        wget \
        gnupg2 && \
    ln -sf /usr/bin/ruby2.7 /usr/bin/ruby && \
    ln -sf /usr/bin/gem2.7 /usr/bin/gem

RUN gem install bundler

RUN mkdir /app
RUN mkdir -p /var/celerybeat

COPY requirements.txt /app/
RUN pip install -r /app/requirements.txt

COPY . /app/
WORKDIR /app

RUN bundle install

CMD gunicorn --workers 3 --worker-class gevent --timeout 30 --max-requests 10000 --max-requests-jitter 100 --limit-request-line 7168 --log-file - -b 0.0.0.0:5000 pombola.wsgi:application
