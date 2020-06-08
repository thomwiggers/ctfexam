"""Registers models with the admin site"""
from django.contrib import admin
from django.utils import timezone

from . import models


class IsActiveListFilter(admin.SimpleListFilter):
    title = "Active challenge"

    parameter_name = "active"

    def lookups(self, *args, **kwargs):
        return (
            ("active", "is active"),
            ("expired", "has expired"),
            ("future", "is planned"),
        )

    def queryset(self, request, queryset):
        if self.value() == "active":
            return queryset.filter(
                start_time__lte=timezone.now(), end_time__gt=timezone.now()
            )
        elif self.value() == "expired":
            return queryset.filter(end_time__lte=timezone.now())
        elif self.value() == "future":
            return queryset.filter(start_time__gte=timezone.now())


@admin.register(models.Challenge)
class ChallengeAdmin(admin.ModelAdmin):
    list_display = ("title", "container", "start_time", "end_time")
    list_filter = (IsActiveListFilter,)


@admin.register(models.ChallengeEntry)
class ChallengeEntryAdmin(admin.ModelAdmin):
    list_display = ("__str__", "completion_time")
    list_filter = ("challenge__title",)


@admin.register(models.ChallengeProcess)
class ChallengeProcessAdmin(admin.ModelAdmin):
    list_display = ("__str__", "running", "started")
    list_filter = ("running",)
    readonly_fields = ("started", "process_identifier")
