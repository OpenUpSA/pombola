from .base import *  # noqa
from .tests_base import *  # noqa
from .south_africa_base import *  # noqa


HAYSTACK_CONNECTIONS['default']['EXCLUDED_INDEXES'] = [
    'pombola.search.search_indexes.PlaceIndex',
    'speeches.search_indexes.SpeechIndex',
]

# Set test index name
HAYSTACK_CONNECTIONS['default']['INDEX_NAME'] = os.environ.get('DATABASE_NAME', 'pombola') + '_test'

INSTALLED_APPS = insert_after(INSTALLED_APPS,
                              'markitup',
                              'pombola.' + COUNTRY_APP)

INSTALLED_APPS += OPTIONAL_APPS

# This is needed by the speeches application
MIDDLEWARE_CLASSES += ( 'pombola.middleware.FakeInstanceMiddleware', )

ENABLED_FEATURES = make_enabled_features(INSTALLED_APPS, ALL_OPTIONAL_APPS)

# For testing purposes we need a cache that we can put stuff in
# to avoid external calls, and generally to avoid polluting the
# cache proper.
CACHES['pmg_api'] = {
    'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    'LOCATION': 'pmg_api_test',
    }

# Ignore tests for the apps that are not installed
DIRECTORIES_TO_IGNORE_FOR_TESTS = ['pombola/kenya', 'pombola/sms']
for app in ALL_OPTIONAL_APPS:
    if app not in INSTALLED_APPS:
        if app.startswith('pombola.'):
            DIRECTORIES_TO_IGNORE_FOR_TESTS.append(app.replace('.', '/'))

for directory in DIRECTORIES_TO_IGNORE_FOR_TESTS:
    NOSE_ARGS += ['--exclude-dir', directory]