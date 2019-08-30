FROM python:2-stretch

ENV PYTHONUNBUFFERED 1
ENV COUNTRY_APP=south_africa

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
                       zlib1g-dev

RUN mkdir /app
COPY requirements.txt /app/
RUN pip install -r /app/requirements.txt

COPY . /app/
# Set WORKDIR after installing, so that src dir isn't created then overwritten
# by development mount
WORKDIR /app

RUN bundle install

ENTRYPOINT ["bin/entrypoint.sh"]

CMD gunicorn --limit-request-line 7168 --worker-class gevent pombola.wsgi:application -t 600 --log-file - -b 0.0.0.0:5000