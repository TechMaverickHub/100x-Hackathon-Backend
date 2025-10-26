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
