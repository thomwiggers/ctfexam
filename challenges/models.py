"""Models for the challenges"""
import logging

from django.dispatch import receiver
from django.db import models
from django.conf import settings
from django.utils.crypto import get_random_string


#: Logger instance
logger = logging.getLogger(__name__)


class Challenge(models.Model):
    """Represents a challenge"""

    title = models.CharField(max_length=100)

    description = models.TextField()

    solution = models.TextField()

    @property
    def completed_entries(self):
        """Return all completed entries of this challenge"""
        return self.challengeentry_set.filter(completion_time__isnull=False)

    def __str__(self):
        return self.title


def random_flag():
    """Return a random, 64-byte string

    >>> len(random_flag())
    64
    >>> random_flag() != random_flag()
    True
    """
    return get_random_string(length=64),


class ChallengeEntry(models.Model):
    """Models a challenge being taken by a user"""

    challenge = models.ForeignKey(
        Challenge,
        on_delete=models.CASCADE,
    )

    #: The flag that completes this challenge
    flag = models.CharField(
        max_length=64,
        default=random_flag,
    )

    #: The user taking this challenge
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE)

    #: When the challenge has been completed
    completion_time = models.DateTimeField(blank=True, null=True)

    writeup = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.user} taking {self.challenge.title}"


class ChallengeProcess(models.Model):
    """Manage a process started for a challenge"""

    challenge_entry = models.ForeignKey(
        "ChallengeEntry",
        on_delete=models.CASCADE,
    )

    running = models.BooleanField(default=False)

    @classmethod
    def start(cls, challenge_entry: ChallengeEntry):
        """Start the process"""
        logger.info("Starting process for %s",
                    challenge_entry.challenge.title)
        cls.objects.create(challenge_entry=challenge_entry, running=True)
    start.alters_data = True

    def stop(self):
        """Stop the process"""
        logger.info("Stopping process for %s",
                    self.challenge_entry.challenge.title)
        self.running = False
        self.save()
    stop.alters_data = True

    def __str__(self):
        return f"Process for {self.challenge_entry}"


@receiver(models.signals.pre_delete, sender=ChallengeProcess,
          dispatch_uid="terminate_process")
def terminate_process_on_delete(sender, instance, **_kwargs):
    """Make sure the process is stopped before we lose track"""
    instance.stop()
