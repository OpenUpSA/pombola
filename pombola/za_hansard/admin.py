from ajax_select import make_ajax_form
from django.contrib import admin
from django.utils.safestring import mark_safe
from django.utils.html import format_html

from pombola.za_hansard import models
from .filters import SuccessfullyParsedFilter


class SourceParsingLogInline(admin.StackedInline):
    model = models.SourceParsingLog

    readonly_fields = [
        'created_at',
        'source',
        'error',
        'success',
        'log',
    ]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(models.Source)
class ZAHansardSourceAdmin(admin.ModelAdmin):
    list_display = [
        'date',
        'pmg_hansard',
        'url',
        'is404',
        'last_processing_success',
        'last_processing_attempt',
    ]

    readonly_fields = [
        'pmg_hansard',
    ]
    date_hierarchy = 'date'
    inlines = [
        SourceParsingLogInline,
    ]

    form = make_ajax_form(models.Source, {
        'sayit_section': 'sayit_section',
    })

    def pmg_hansard(self, obj):
        return mark_safe('<a href="https://api.pmg.org.za/hansard/{}/">{}</a>'.format(
            obj.pmg_id,
            obj.pmg_id
        )) if obj.pmg_id is not None else None

    list_filter = [SuccessfullyParsedFilter, 'is404', 'date']

@admin.register(models.QuestionParsingError)
class QuestionParsingErrorAdmin(admin.ModelAdmin):
    search_fields = ('pmg_url', )
    list_display = ['error_type', 'pmg_api_url_link', 'last_seen']
    list_filter = ['error_type',]
    actions = None

    def pmg_api_url_link(self, obj):
        return format_html("<a href='{url}'>{url}</a>", url=obj.pmg_url)
    pmg_api_url_link.short_description = "PMG API URL"

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
