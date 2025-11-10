from rest_framework import serializers

from pages.models import PageSection, SiteStat


class PageSectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PageSection
        fields = ["id", "slug", "title", "description", "cta_label", "cta_link", "order", "updated_at"]


class SiteStatSerializer(serializers.ModelSerializer):
    class Meta:
        model = SiteStat
        fields = ["id", "name", "value", "unit", "description"]
