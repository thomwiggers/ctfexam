from datetime import timedelta

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from challenges import models


class Command(BaseCommand):
    help = "Cleans up no-longer running procesess"

    def handle(self, *args, **kwargs):
        for process in models.ChallengeProcess.running_challenges.all():
            if timezone.now() - process.started > timedelta(hours=12):
                process.stop()

        models.ChallengeProcess.cleanup()
