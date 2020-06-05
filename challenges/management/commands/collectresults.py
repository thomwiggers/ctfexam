from datetime import timedelta
from pathlib import Path
import json
import shutil

from django.core.management.base import BaseCommand, CommandError
from django.template import loader
from django.utils import timezone
from django.utils.text import slugify
from django.conf import settings

from challenges.models import ChallengeEntry


def find_student_numbers(text, mine):
    text = text.lower()
    found = []
    if settings.VALID_STUDENT_NUMBERS is None:
        return
    for student_number in settings.VALID_STUDENT_NUMBERS:
        if student_number != mine and student_number in text:
            found.append(student_number)
    if found:
        return found
    # try again without leading letter
    for student_number in settings.VALID_STUDENT_NUMBERS:
        if student_number[1:] in text:
            found.append(student_number)
    if found:
        return found


class Command(BaseCommand):
    help = "Collect results for students"

    def handle(self, *args, **kwargs):
        logdir = settings.MEDIA_ROOT / "logs"
        base_dir = Path("challenges/collect")
        writeup_template = loader.get_template(base_dir / "writeup.md")
        challenge_template = loader.get_template(base_dir / "challenge.md")
        output_dir = Path("collected")
        for entry in ChallengeEntry.objects.all():
            user = entry.user
            full_name = slugify(user.get_full_name())
            user_dir = output_dir / f"{user.student_number}_{full_name}"
            challenge_dir = user_dir / slugify(entry.challenge.title)
            challenge_dir.mkdir(parents=True)

            partners = None
            if entry.writeup:
                partners = find_student_numbers(entry.writeup, user.student_number)

            with open(challenge_dir / "challenge.md", "w") as f:
                f.write(challenge_template.render({"challenge": entry.challenge}))
            with open(challenge_dir / "writeup.md", "w") as f:
                f.write(
                    writeup_template.render(
                        {
                            "entry": entry,
                            "settings": json.dumps(entry.settings, indent=2),
                            "user": user,
                            "partners": partners,
                        }
                    )
                )

            if partners is not None:
                with open(challenge_dir / "partners.txt", "w") as f:
                    f.write("\n".join(partners))

            for num, proc in enumerate(
                entry.challengeprocess_set.order_by("started", "process_identifier")
            ):
                logfile = logdir / proc.process_identifier / "challenge.log"
                if logfile.exists():
                    shutil.copyfile(logfile, challenge_dir / f"log-{num}.log")
