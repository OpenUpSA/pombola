import os
import subprocess
from django.conf import settings
from django.contrib.sites.models import Site


def add_settings( request ):
    """Add some selected settings values to the context"""
    return {
        'settings': {
            'STAGING':                      settings.STAGING,
            'GOOGLE_ANALYTICS_ACCOUNT':     settings.GOOGLE_ANALYTICS_ACCOUNT,
            'GOOGLE_ANALYTICS_ID':          settings.GOOGLE_ANALYTICS_ID,
            'POLLDADDY_WIDGET_ID':          settings.POLLDADDY_WIDGET_ID,
            'DISQUS_SHORTNAME':             settings.DISQUS_SHORTNAME,
            'DISQUS_USE_IDENTIFIERS':       settings.DISQUS_USE_IDENTIFIERS,
            'TWITTER_USERNAME':             settings.TWITTER_USERNAME,
            'TWITTER_WIDGET_ID':            settings.TWITTER_WIDGET_ID,
            'BLOG_RSS_FEED':                settings.BLOG_RSS_FEED,
            'ENABLED_FEATURES':             settings.ENABLED_FEATURES,
            'COUNTRY_APP':                  settings.COUNTRY_APP,
            'MAP_BOUNDING_BOX_NORTH':       settings.MAP_BOUNDING_BOX_NORTH,
            'MAP_BOUNDING_BOX_EAST':        settings.MAP_BOUNDING_BOX_EAST,
            'MAP_BOUNDING_BOX_SOUTH':       settings.MAP_BOUNDING_BOX_SOUTH,
            'MAP_BOUNDING_BOX_WEST':        settings.MAP_BOUNDING_BOX_WEST,
            'POPIT_API_URL':                settings.POPIT_API_URL,
            'FACEBOOK_APP_ID':              settings.FACEBOOK_APP_ID,
            'GOOGLE_SITE_VERIFICATION':     settings.GOOGLE_SITE_VERIFICATION,
            'GOOGLE_RECAPTCHA_SITE_KEY':    settings.GOOGLE_RECAPTCHA_SITE_KEY,
        }
    }


def site_processor(request):
    return {'site': Site.objects.get_current()}


def deployment_info(request):
    hostname = os.environ.get('HOSTNAME', 'unknown')

    git_commit = 'unknown'
    try:
        git_commit = subprocess.check_output(
            ['git', 'rev-parse', '--short', 'HEAD'],
            stderr=subprocess.DEVNULL,
            timeout=1
        ).decode('utf-8').strip()
    except:
        pass

    return {
        'deployment': {
            'hostname': hostname,
            'git_commit': git_commit,
        }
    }
