from __future__ import absolute_import
from django.contrib import admin
from . import models

@admin.register(models.Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display  = [ 'cdf_index', 'constituency', 'project_name' ]
    search_fields = [ 'constituency__name', 'project_name' ]
