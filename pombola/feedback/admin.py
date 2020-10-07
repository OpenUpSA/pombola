from django.contrib import admin
from django.contrib import messages
from pombola.feedback.models import Feedback
from django.utils.translation import ngettext

@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):

    list_display = ('status', 'comment', 'user', 'email', 'url', 'created',)
    list_filter = ('created', 'status')
    date_hierarchy = 'created'
    ordering = ('-created',)
    raw_id_fields = ('user',)
    search_fields = ('comment', 'user__username', 'url', 'email')
    actions = ['mark_as_spammy']

    def mark_as_spammy(self, request, queryset):
        updated = queryset.update(status='spammy')
        self.message_user(request, ngettext(
            '%d feedback item was successfully marked as spam.',
            '%d feedback items were successfully marked as spam.',
            updated,
        ) % updated, messages.SUCCESS)

    mark_as_spammy.short_description = "Mark selected feedback as spam"
