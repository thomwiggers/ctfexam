from django.contrib.auth.forms import UserCreationForm as BaseUserCreationForm

from . import models

class UserCreationForm(BaseUserCreationForm):

    class Meta(BaseUserCreationForm.Meta):
        model = models.User
        fields = BaseUserCreationForm.Meta.fields + ('student_number',)
