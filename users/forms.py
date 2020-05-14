from django.contrib.auth.forms import UserCreationForm as BaseUserCreationForm

from . import models

class UserCreationForm(BaseUserCreationForm):

    class Meta(BaseUserCreationForm.Meta):
        model = models.User
        fields = [
            'first_name', 'last_name', 'email', 'student_number',
            'password1', 'password2',
        ]
