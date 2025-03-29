# shortener/admin.py

from django.contrib import admin
from .models import ShortURL, ClickEvent

class ShortURLAdmin(admin.ModelAdmin):
    list_display = ('short_code', 'original_url', 'created_at', 'expiration_date', 'is_active', 'user')
    list_filter = ('is_active', 'created_at')
    search_fields = ('short_code', 'original_url', 'user__username')
    actions = ['mark_as_harmful']

    def mark_as_harmful(self, request, queryset):
        queryset.update(is_active=False)
        self.message_user(request, "Selected URLs marked as harmful and deactivated.")

    mark_as_harmful.short_description = "Mark selected URLs as harmful and deactivate"

class ClickEventAdmin(admin.ModelAdmin):
    list_display = ('short_url', 'timestamp', 'ip_address', 'user_agent', 'referrer')
    list_filter = ('timestamp',)
    search_fields = ('ip_address', 'user_agent', 'referrer')

admin.site.register(ShortURL, ShortURLAdmin)
admin.site.register(ClickEvent, ClickEventAdmin)
