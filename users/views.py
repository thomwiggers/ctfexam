from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic.edit import FormView

from . import forms


class UserRegistration(FormView):
    template_name = 'ctf/form.html'
    form_class = forms.UserCreationForm
    success_url = reverse_lazy('index')

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)
