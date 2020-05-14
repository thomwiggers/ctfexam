from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.

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
    )
