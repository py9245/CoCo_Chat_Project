from django.db import models


class PageSection(models.Model):
    slug = models.SlugField(unique=True)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    cta_label = models.CharField(max_length=120, blank=True)
    cta_link = models.URLField(blank=True)
    order = models.PositiveSmallIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.title


class SiteStat(models.Model):
    name = models.CharField(max_length=100, unique=True)
    value = models.PositiveIntegerField(default=0)
    unit = models.CharField(max_length=50, blank=True)
    description = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name}: {self.value}{self.unit}"
