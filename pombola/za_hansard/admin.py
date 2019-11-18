from django.contrib import admin

from pombola.za_hansard import models

admin.site.register(models.ZAHansardParsingLog)
admin.site.register(models.Source)
