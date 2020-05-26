"""Models for the challenges"""
from pathlib import Path
import os
import logging
import random
import secrets

from django.dispatch import receiver
from django.db import models, transaction
from django.db.models import Q
from django.conf import settings as django_settings
from django.utils.crypto import get_random_string
from django.utils.text import slugify
from django.utils import timezone
from django.urls import reverse

import docker


#: Logger instance
logger = logging.getLogger(__name__)


class Challenge(models.Model):
    """Represents a challenge"""

    title = models.CharField(max_length=100)

    description = models.TextField()

    solution = models.TextField()

    container = models.CharField(max_length=255)

    @property
    def completed_entries(self):
        """Return all completed entries of this challenge"""
        return self.challengeentry_set.filter(completion_time__isnull=False)

    def get_absolute_url(self):
        return reverse('challenges:challenge', kwargs={'pk': self.pk})

    def __str__(self):
        return self.title


def random_settings():
    """Return randomized settings for the challenge

    >>> random_settings()  # doctest: +ELLIPSIS
    {'flag': ...
    >>> random_settings() != random_settings()
    True
    """
    return {
        'flag': f"HiCCTF{{{get_random_string(length=64)}}}",
        'buffer_padding': random.randint(1, 75)
    }


class ChallengeEntry(models.Model):
    """Models a challenge being taken by a user"""

    challenge = models.ForeignKey(
        Challenge,
        on_delete=models.CASCADE,
    )

    #: The flag that completes this challenge
    settings = models.JSONField(
        default=random_settings,
    )

    #: The user taking this challenge
    user = models.ForeignKey(django_settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE)

    #: When the challenge has been completed
    completion_time = models.DateTimeField(blank=True, null=True)

    writeup = models.TextField(blank=True, null=True)

    @property
    def flag(self):
        return self.settings.get('flag', get_random_string(length=64))

    def submit_flag(self, flag):
        if flag is None:
            return False
        if secrets.compare_digest(self.flag, flag):
            self.completion_time = timezone.now()
            self.save()
            return True
        return False

    def __str__(self):
        return f"{self.user} taking {self.challenge.title}"


class AvailablePortsManager(models.Manager):
    def get_queryset(self):
        return (super()
                .get_queryset()
                .filter(
                    Q(challengeprocess__running=True) |
                    Q(challengeprocess__isnull=True)))


class Port(models.Model):
    """Manages available ports"""

    objects = models.Manager()
    available_ports = AvailablePortsManager()

    port = models.PositiveIntegerField(primary_key=True)

    @classmethod
    def get_new_port(cls):
        return cls.available_ports.order_by('?').first()


class ActiveChallengesManager(models.Manager):
    """Gets only active challenges"""

    def get_queryset(self):
        """Filter on running instances"""
        return super().get_queryset().filter(running=True)


class ChallengeProcess(models.Model):
    """Manage a process started for a challenge"""

    objects = models.Manager()
    running_challenges = ActiveChallengesManager()

    challenge_entry = models.ForeignKey(
        "ChallengeEntry",
        on_delete=models.CASCADE,
    )

    running = models.BooleanField(default=False)

    port = models.OneToOneField(Port, blank=True, null=True,
                                on_delete=models.PROTECT)

    process_identifier = models.TextField()

    @classmethod
    def cleanup(cls):
        """Remove all stale process handles"""
        client = docker.DockerClient.from_env()
        for process in cls.running_challenges.all():
            dockerid = process.process_identifier
            try:
                client.containers.get(f'{dockerid}_vuln')
            except docker.errors.NotFound:
                process.running = False
                process.save()
    cleanup.alters_data = True

    @classmethod
    def start(cls, challenge_entry: ChallengeEntry):
        """Start the process"""
        logger.info("Starting process for %s",
                    challenge_entry.challenge.title)

        challenge = challenge_entry.challenge
        dockerid = (f'{slugify(challenge.title)}'
                    f'_{challenge_entry.user.username}'
                    f'_{get_random_string(32)}')

        logdir = django_settings.MEDIA_ROOT / 'logs' / dockerid
        logdir.mkdir(parents=True)

        client = docker.DockerClient.from_env()
        client.images.pull(django_settings.PROXY_CONTAINER, tag='latest')
        challenge_container = (
            f"{django_settings.CONTAINER_NAMESPACE}/{challenge.container}")
        client.images.pull(challenge_container, tag='latest')
        internal = client.networks.create(
            f'{dockerid}_internal_network',
            internal=True,
        )
        client.networks.create(
            f'{dockerid}_public_network',
        )
        vuln = client.containers.run(
            challenge_container,
            name=f'{dockerid}_vuln',
            detach=True,
            auto_remove=True,
            cpu_quota=5000,  # 5%
            mem_limit='50m',
            network_mode=None,
            hostname='vulnhost',
            stop_signal='SIGKILL',
            pids_limit=5,
            privileged=True,
            cap_drop=['ALL'],
            environment={
                key.upper(): value
                for key, value in challenge_entry.settings.items()
            },
        )
        with transaction.atomic():
            port = Port.get_new_port()
            proxy = client.containers.run(
                django_settings.PROXY_CONTAINER,
                name=f'{dockerid}_proxy',
                detach=True,
                auto_remove=True,
                cpu_quota=5000,  # 5%
                mem_limit='50m',
                network=f'{dockerid}_public_network',
                stop_signal='SIGKILL',
                cap_add=['CHOWN'],
                environment={
                    'VULNHOST': 'vulnhost',
                    'VULNPORT': '1337',
                },
                ports={
                    '4000': port.port,
                },
                volumes={
                    str(logdir): {'bind': '/log/', 'mode': 'rw'},
                },
            )
            internal.connect(proxy)
            internal.connect(vuln, aliases=['vulnhost'])

            cls.objects.create(
                challenge_entry=challenge_entry,
                process_identifier=dockerid,
                port=port,
                running=True)
    start.alters_data = True

    def stop(self):
        """Stop the process"""
        logger.info("Stopping process for %s",
                    self.challenge_entry.challenge.title)
        client = docker.DockerClient.from_env()
        dockerid = self.process_identifier

        try:
            for name in ['vuln', 'proxy']:
                container = client.containers.get(f'{dockerid}_{name}')
                container.stop(timeout=2)
            for name in ['internal', 'public']:
                network = client.networks.get(f'{dockerid}_{name}_network')
                network.remove()
        except docker.errors.NotFound:
            logger.exception("Couldn't finish cleanup")
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
