# shortener/models.py

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class ShortURL(models.Model):
    original_url = models.URLField(max_length=2000)
    short_code = models.CharField(max_length=10, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    expiration_date = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    tags = models.CharField(max_length=255, blank=True, null=True)
    category = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return self.short_code

    def is_expired(self):
        if self.expiration_date and timezone.now() > self.expiration_date:
            return True
        return False

class ClickEvent(models.Model):
    short_url = models.ForeignKey(ShortURL, on_delete=models.CASCADE, related_name='clicks')
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.CharField(max_length=255)
    referrer = models.URLField(null=True, blank=True)

    def __str__(self):
        return f"Click on {self.short_url.short_code} at {self.timestamp}"

class DashboardPreference(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    show_clicks = models.BooleanField(default=True)
    show_expiration = models.BooleanField(default=True)
    show_tags = models.BooleanField(default=True)
    show_category = models.BooleanField(default=True)

    def __str__(self):
        return f"Preferences for {self.user.username}"
