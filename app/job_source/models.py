from django.contrib.auth import get_user_model
from django.db import models

# Create your models here.
class Source(models.Model):


    # Fields
    name = models.CharField(max_length=100)
    api_url = models.URLField(blank=True, null=True)
    rss_url = models.URLField(blank=True, null=True)

    # Additional Fields
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)


class UserSource(models.Model):

    # Foreign key
    user = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        related_name="job_sources",  # all sources a user is subscribed to
        related_query_name="job_source"
    )
    source = models.ForeignKey(
        Source,
        on_delete=models.CASCADE,
        related_name="subscribed_users",  # all users subscribed to this source
        related_query_name="subscribed_user"
    )

    # Field declarations
    frequency = models.CharField(
        max_length=20,
        choices=[('once', 'Once'), ('daily', 'Daily'), ('weekly', 'Weekly'), ('monthly', 'Monthly')],
        default='once'
    )

    alert = models.BooleanField(default=True)

    # Additional Fields
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)