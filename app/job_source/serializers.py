from rest_framework import serializers

from app.job_source.models import Source, UserSource


class SourceCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Source
        fields = ('pk', 'name', 'api_url', 'rss_url', )


class SourceDisplaySerializer(serializers.ModelSerializer):
    class Meta:
        model = Source
        fields = ('pk', 'name', 'api_url', 'rss_url', 'created')


class SourceUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Source
        fields = ( 'name', 'api_url', 'rss_url',)


class SourceListFilterDisplaySerializer(serializers.ModelSerializer):
    class Meta:
        model = Source
        fields = ('pk', 'name', 'api_url', 'rss_url', 'created')


class SourceListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Source
        fields = ('pk', 'name',)

class UserSourceSelectSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserSource
        fields = ('pk', 'user', 'source', 'frequency', 'alert')


class UserSourceSelectDisplaySerializer(serializers.ModelSerializer):

    source = SourceDisplaySerializer()
    class Meta:
        model = UserSource
        fields = ('pk', 'source', 'frequency', 'alert')