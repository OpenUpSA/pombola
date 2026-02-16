FROM python:3.9.22-bookworm

ENV PYTHONUNBUFFERED 1
ENV COUNTRY_APP=south_africa

RUN echo "deb http://deb.debian.org/debian bullseye main" > /etc/apt/sources.list.d/bullseye.list && \
    rm -rf /var/lib/apt/lists/* && \
    apt-get update && \
    apt-get install -y antiword \
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
            ruby2.7 \
            ruby2.7-dev \
            yui-compressor \
            zlib1g-dev \
            postgresql-client \
            awscli \
            wget && \
    ln -sf /usr/bin/ruby2.7 /usr/bin/ruby && \
    ln -sf /usr/bin/gem2.7 /usr/bin/gem

RUN gem install bundler

RUN mkdir /app
RUN mkdir -p /var/celerybeat

COPY requirements.txt /app/
RUN pip install -r /app/requirements.txt

# Monkey patching
# django-slug-helpers add on_delete to ForeignKeys for Django 3.2 compatibility
RUN sed -i "s/models.ForeignKey(ContentType)/models.ForeignKey(ContentType, on_delete=models.CASCADE)/" \
    /usr/local/lib/python3.9/site-packages/slug_helpers/models.py && \
    sed -i "s/models.ForeignKey(to='contenttypes.ContentType')/models.ForeignKey(to='contenttypes.ContentType', on_delete=models.CASCADE)/" \
    /usr/local/lib/python3.9/site-packages/slug_helpers/migrations/0001_initial.py

# Add python_2_unicode_compatible back to Django's encoding module as a no-operation
RUN printf '\ndef python_2_unicode_compatible(cls):\n    return cls\n' >> \
    /usr/local/lib/python3.9/site-packages/django/utils/encoding.py

# Create django.utils.six shim
RUN printf 'from six import *\nfrom six import moves\n' > \
    /usr/local/lib/python3.9/site-packages/django/utils/six.py

# Sluggable, FieldDoesNotExist moved to django.core.exceptions
RUN sed -i 's/from django.db.models.fields import FieldDoesNotExist, DateField/from django.core.exceptions import FieldDoesNotExist\nfrom django.db.models.fields import DateField/' \
    /usr/local/lib/python3.9/site-packages/sluggable/utils.py

# Add available_attrs to django.utils.decorators
RUN printf '\nimport functools\ndef available_attrs(fn):\n    return functools.WRAPPER_ASSIGNMENTS\n' >> \
    /usr/local/lib/python3.9/site-packages/django/utils/decorators.py

# django-select2, staticfiles.static 
RUN sed -i 's|from django.contrib.staticfiles.templatetags.staticfiles import static|from django.templatetags.static import static|' \
    /src/mysociety-django-select2/django_select2/media.py

# django-pagination, TOKEN_BLOCK moved to TokenType.BLOCK
RUN sed -i 's/from django.template.base import TOKEN_BLOCK/from django.template.base import TokenType; TOKEN_BLOCK = TokenType.BLOCK/' \
    /src/mysociety-django-pagination/pagination/templatetags/pagination_tags.py

# PaginationMiddleware, add new middleware
RUN echo 'from django.utils.deprecation import MiddlewareMixin' > /src/mysociety-django-pagination/pagination/middleware.py && \
    echo 'def get_page(self, suffix):' >> /src/mysociety-django-pagination/pagination/middleware.py && \
    echo '    try:' >> /src/mysociety-django-pagination/pagination/middleware.py && \
    echo '        key = "page%s" % suffix' >> /src/mysociety-django-pagination/pagination/middleware.py && \
    echo '        return int(self.GET.get(key) or self.POST.get(key))' >> /src/mysociety-django-pagination/pagination/middleware.py && \
    echo '    except (KeyError, ValueError, TypeError):' >> /src/mysociety-django-pagination/pagination/middleware.py && \
    echo '        return 1' >> /src/mysociety-django-pagination/pagination/middleware.py && \
    echo 'class PaginationMiddleware(MiddlewareMixin):' >> /src/mysociety-django-pagination/pagination/middleware.py && \
    echo '    def process_request(self, request):' >> /src/mysociety-django-pagination/pagination/middleware.py && \
    echo '        request.__class__.page = get_page' >> /src/mysociety-django-pagination/pagination/middleware.py

COPY . /app/
WORKDIR /app

RUN bundle install

CMD gunicorn --workers 3 --worker-class gevent --timeout 30 --max-requests 10000 --max-requests-jitter 100 --limit-request-line 7168 --log-file - -b 0.0.0.0:5000 pombola.wsgi:application
