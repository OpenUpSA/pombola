FROM python:2-stretch

ENV PYTHONUNBUFFERED 1
ENV COUNTRY_APP=south_africa

RUN echo "deb http://archive.debian.org/debian/ stretch main" > /etc/apt/sources.list \
    && echo "deb http://archive.debian.org/debian-security stretch/updates main" >> /etc/apt/sources.list \
    && apt-get -o Acquire::Check-Valid-Until=false update

RUN apt-get update && \
    apt-get install -y antiword \
                       binutils \
                       libffi-dev \
                       libjpeg-dev \
                       libpq-dev \
                       libxml2-dev \
                       libxslt1-dev \
                       libproj-dev \
                       gdal-bin \
                       poppler-utils \
                       python-dev \
                       python-gdal \
                       ruby-bundler \
                       ruby2.3-dev \
                       yui-compressor \
                       zlib1g-dev \
                       postgresql-client \
                       awscli

RUN mkdir /app
RUN mkdir -p /var/celerybeat

COPY requirements.txt /app/
RUN pip install -r /app/requirements.txt

COPY . /app/
# Set WORKDIR after installing, so that src dir isn't created then overwritten
# by development mount
WORKDIR /app

RUN bundle install

CMD gunicorn --workers 3 --worker-class gevent --timeout 30 --max-requests 10000 --max-requests-jitter 100 --limit-request-line 7168 --log-file - -b 0.0.0.0:5000 pombola.wsgi:application
