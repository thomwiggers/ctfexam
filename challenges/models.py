"""Models for the challenges"""
import logging
import random
import secrets

import docker
from django import forms
from django.dispatch import receiver
from django.db import models, transaction
from django.db.models import Q
from django.conf import settings as django_settings
from django.utils.crypto import get_random_string
from django.utils.text import slugify
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.core import validators
from django.urls import reverse


#: Logger instance
logger = logging.getLogger(__name__)


class AvailableChallengeManager(models.Manager):
    """Available challenges"""

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(start_time__lte=timezone.now(), end_time__gt=timezone.now())
        )


def ports_default():
    """Default ports"""
    return [{"port": 1337, "description": "challenge port", "logged": True,}]


class Challenge(models.Model):
    """Represents a challenge"""

    objects = models.Manager()
    available = AvailableChallengeManager()

    title = models.CharField(max_length=100)

    description = models.TextField()

    solution = models.TextField()

    container = models.CharField(max_length=255)

    start_time = models.DateTimeField(
        help_text="available from this time", default=timezone.now
    )

    end_time = models.DateTimeField("no longer available after")

    listen_ports = models.JSONField(
        _("Ports exposed by this container"),
        help_text=_("Port, description and if it's logged"),
        default=ports_default,
    )

    privileged = models.BooleanField(
        _("Needs privileged container"),
        help_text=_("containers that disable ASLR need this."),
        default=False,
    )

    @property
    def is_active(self):
        """Is this challenge currently active?"""
        now = timezone.now()
        return self.start_time <= now < self.end_time

    @property
    def completed_entries(self):
        """Return all completed entries of this challenge"""
        return self.challengeentry_set.filter(completion_time__isnull=False)

    def get_absolute_url(self):
        return reverse("challenges:challenge", kwargs={"pk": self.pk})

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
        "flag": f"HiCCTF{{{get_random_string(length=64)}}}",
        "buffer_padding": random.randint(1, 75),
        "memory_padding": "A" * random.randint(1, 200),
    }


class ChallengeEntry(models.Model):
    """Models a challenge being taken by a user"""

    challenge = models.ForeignKey(Challenge, on_delete=models.CASCADE)

    #: The flag that completes this challenge
    settings = models.JSONField(default=random_settings)

    #: The user taking this challenge
    user = models.ForeignKey(django_settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    #: When the challenge has been completed
    completion_time = models.DateTimeField(blank=True, null=True)

    writeup = models.TextField(blank=True, null=True)

    @property
    def flag(self):
        return self.settings.get("flag", get_random_string(length=64))

    def submit_flag(self, flag):
        if flag is None or not flag.isascii():
            return False
        if secrets.compare_digest(self.flag, flag):
            self.completion_time = timezone.now()
            self.save()
            return True
        return False

    def __str__(self):
        return f"{self.user} taking {self.challenge.title}"


class ActiveChallengesManager(models.Manager):
    """Gets only active challenges"""

    def get_queryset(self):
        """Filter on running instances"""
        return super().get_queryset().filter(running=True)


class ChallengeProcess(models.Model):
    """Manage a process started for a challenge"""

    objects = models.Manager()

    running_challenges = ActiveChallengesManager()

    challenge_entry = models.ForeignKey("ChallengeEntry", on_delete=models.CASCADE)

    running = models.BooleanField(default=False)

    process_identifier = models.TextField()

    started = models.DateTimeField(auto_now_add=True)

    @property
    def ports(self):
        """Get the remotely accessible port"""
        if not self.running:
            return []
        client = docker.DockerClient.from_env()
        external_ports = []

        try:
            listen_ports = self.challenge_entry.challenge.listen_ports
            for port_data in listen_ports:
                port = port_data["port"]
                if port_data["logged"]:
                    cont = client.containers.get(
                        f"{self.process_identifier}_proxy_{port}"
                    )
                    internal_port = "4000/tcp"
                else:
                    cont = client.containers.get(f"{self.process_identifier}_vuln")
                    internal_port = f"{port}/tcp"
                cont.reload()
                external_ports.append(
                    {
                        "port": cont.ports.get(internal_port, [{"HostPort": None}])[0][
                            "HostPort"
                        ],
                        "description": port_data["description"],
                    }
                )
        except docker.errors.NotFound:
            self.stop()
        return external_ports

    @classmethod
    def cleanup(cls):
        """Remove all stale process handles"""
        client = docker.DockerClient.from_env()
        for process in cls.running_challenges.all():
            dockerid = process.process_identifier
            try:
                client.containers.get(f"{dockerid}_vuln")
            except docker.errors.NotFound:
                process.stop(client)

    cleanup.alters_data = True

    @classmethod
    def start(cls, challenge_entry: ChallengeEntry):
        """Start the process"""
        logger.info("Starting process for %s", challenge_entry.challenge.title)

        challenge = challenge_entry.challenge
        dockerid = (
            f"{slugify(challenge.title)}"
            f"_{slugify(challenge_entry.user.username)}"
            f"_{timezone.now().strftime('%Y%m%d-%H%M%S')}"
            f"_{get_random_string(16)}"
        )

        logdir = django_settings.MEDIA_ROOT / "logs" / dockerid
        logdir.mkdir(parents=True)

        client = docker.DockerClient.from_env()
        client.images.pull(django_settings.PROXY_CONTAINER, tag="latest")
        challenge_container = (
            f"{django_settings.CONTAINER_NAMESPACE}/{challenge.container}"
        )
        client.images.pull(challenge_container, tag="latest")
        internal = client.networks.create(
            f"{dockerid}_internal_network", internal=True,
        )
        client.networks.create(f"{dockerid}_public_network",)
        public_ports = {
            port["port"]: None for port in challenge.listen_ports if not port["logged"]
        }
        vuln = client.containers.run(
            challenge_container,
            name=f"{dockerid}_vuln",
            detach=True,
            auto_remove=False,
            cpu_period=100000,
            cpu_quota=5000,  # 5%
            mem_limit="150m",
            network_mode=None,
            hostname="vulnhost",
            stop_signal="SIGKILL",
            pids_limit=100,
            privileged=challenge.privileged,
            ports=public_ports,
            cap_drop=["ALL"],
            cap_add=["NET_BIND_SERVICE", "CHOWN", "SETUID", "SETGID", "SYS_CHROOT", "AUDIT_WRITE", "DAC_OVERRIDE"],
            environment={
                key.upper(): value for key, value in challenge_entry.settings.items()
            },
        )
        with transaction.atomic():
            for port in challenge.listen_ports:
                if not port["logged"]:
                    continue
                proxy = client.containers.run(
                    django_settings.PROXY_CONTAINER,
                    name=f"{dockerid}_proxy_{port['port']}",
                    detach=True,
                    auto_remove=True,
                    cpu_period=100000,
                    cpu_quota=10000,  # 10%
                    mem_limit="100m",
                    network=f"{dockerid}_public_network",
                    stop_signal="SIGKILL",
                    cap_add=["CHOWN"],
                    environment={
                        "VULNHOST": "vulnhost",
                        "VULNPORT": f"{port['port']}",
                    },
                    ports={"4000": None},
                    volumes={str(logdir): {"bind": "/log/", "mode": "rw"},},
                )
                internal.connect(proxy)

            internal.connect(vuln, aliases=["vulnhost"])
            cls.objects.create(
                challenge_entry=challenge_entry,
                process_identifier=dockerid,
                running=True,
            )

    start.alters_data = True

    def stop(self, client=None):
        """Stop the process"""
        logger.info("Stopping process for %s", self.challenge_entry.challenge.title)
        if client is None:
            client = docker.DockerClient.from_env()
        dockerid = self.process_identifier

        def stop_container(name):
            try:
                container = client.containers.get(f"{dockerid}_{name}")
                container.stop(timeout=2)
            except docker.errors.NotFound:
                logger.exception("Container %s_%s already stopped", dockerid, name)

        def remove_network(name):
            try:
                network = client.networks.get(f"{dockerid}_{name}_network")
                network.remove()
            except docker.errors.NotFound:
                pass

        stop_container("vuln")
        for port in self.challenge_entry.challenge.listen_ports:
            stop_container(f"proxy_{port['port']}")
        for name in ["internal", "public"]:
            remove_network(name)

        self.running = False
        self.save()

    stop.alters_data = True

    def __str__(self):
        return f"Process for {self.challenge_entry}"


@receiver(
    models.signals.pre_delete, sender=ChallengeProcess, dispatch_uid="terminate_process"
)
def terminate_process_on_delete(sender, instance, **_kwargs):
    """Make sure the process is stopped before we lose track"""
    instance.stop()
