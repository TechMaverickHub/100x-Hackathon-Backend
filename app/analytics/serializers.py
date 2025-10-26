from rest_framework import serializers

from app.analytics.models import AIAnalytics


class AIAnalyticsListFilterDisplaySerializer(serializers.ModelSerializer):

    class Meta:
        model = AIAnalytics
        fields = ('pk', 'generation_type', 'content', 'created')