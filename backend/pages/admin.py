from django.contrib import admin

from pages.models import PageSection, SiteStat


@admin.register(PageSection)
class PageSectionAdmin(admin.ModelAdmin):
    list_display = ("title", "slug", "order", "updated_at")
    prepopulated_fields = {"slug": ("title",)}
    list_editable = ("order",)


@admin.register(SiteStat)
class SiteStatAdmin(admin.ModelAdmin):
    list_display = ("name", "value", "unit")
