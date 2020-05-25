from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth.models import AbstractUser
from django.conf import settings

# Create your models here.


def validate_student_number(student_number):
    if (numbers := settings.get('VALID_STUDENT_NUMBERS')) is not None:
        if student_number not in numbers:
            raise ValidationError("This is not a known student number")


class User(AbstractUser):
    REQUIRED_FIELDS = [
        'first_name',
        'last_name',
        'email',
        'student_number',
    ]

    student_number = models.CharField(
        'student number',
        max_length=8,
        blank=False,
        null=False,
        unique=True,
        validators=[
            validate_student_number,
        ],
    )
