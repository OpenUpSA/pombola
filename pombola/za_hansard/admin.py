from django.contrib import admin
from django.core import urlresolvers
from django.utils.safestring import mark_safe  

from pombola.za_hansard import models
from .filters import SuccessfullyParsedFilter

@admin.register(models.ZAHansardParsingLog)
class ZAHansardParsingLogAdmin(admin.ModelAdmin):
    list_display = [
        'date',
        'linked_source',
        'source_url',
        'error',
        'success',
        ]

    list_filter = ['error', 'success', 'date',]
    readonly_fields = [
        'date',
        'source',
        'error',
        'success', 
        'log',
        'source',
        'linked_source'
        ]
    actions = []
    date_hierarchy = 'date'

    def source_url(self, obj):
        return mark_safe('<a href="{}">{}</a>'.format(
            obj.source.url,
            obj.source.url
        ))

    def linked_source(self, obj):
        return mark_safe('<a href="{}">{}</a>'.format(
            urlresolvers.reverse("admin:za_hansard_source_change", args=(obj.source.pk,)),
            obj.source
        ))

@admin.register(models.Source)
class ZAHansardSourceAdmin(admin.ModelAdmin):
    list_display = [
        'date',
        'url',
        'is404',
        'last_processing_success',
        'last_processing_attempt',
        ]


    list_filter = [SuccessfullyParsedFilter, 'is404', 'date']