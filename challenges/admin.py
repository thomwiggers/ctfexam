"""Registers models with the admin site"""
from django.contrib import admin

from . import models


admin.site.register(models.Challenge)
admin.site.register(models.ChallengeEntry)
admin.site.register(models.ChallengeProcess)
