from django.core.management.base import BaseCommand, CommandError
from challenges import models


class Command(BaseCommand):
    help = 'Cleans up no-longer running procesess'

    def handle(self, *args, **kwargs):
        models.ChallengeProcess.cleanup()
