from html import unescape
from typing import Dict

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse, Http404
from django.views.generic import TemplateView, DetailView, View
from django.views.generic.edit import CreateView
from django.shortcuts import render, get_object_or_404
from django.conf import settings

import markdown
import bleach


from . import models


def markdownize(text):
    if text is not None:
        return markdown.markdown(text, extensions=["extra", "smarty", "codehilite"],)
    return ""


class ChallengeListView(TemplateView):
    """List of challenges"""

    template_name = "challenges/challenge_list.html"

    def _format_challenge(self, challenge: models.Challenge) -> Dict:
        user = self.request.user
        try:
            if not user.is_anonymous:
                user_entry = challenge.completed_entries.get(user=user)
                finished = user_entry.completion_time is not None and user_entry.writeup
            else:
                user_entry = None
                finished = None
        except models.ChallengeEntry.DoesNotExist:
            user_entry = None
            finished = False

        return {
            "obj": challenge,
            "finished": finished,
            "user_entry": user_entry,
        }

    def get_context_data(self, *args, **kwargs):
        """Get the data necessary for the view"""
        if self.request.user.is_superuser:
            challenges = models.Challenge.objects.all()
        else:
            challenges = models.Challenge.available.all()
        context = super().get_context_data(*args, **kwargs)
        context["challenges"] = [
            self._format_challenge(challenge)
            for challenge in challenges
        ]

        return context


class ChallengeDetailView(LoginRequiredMixin, DetailView):
    def get_queryset(self):
        # Needs to be active because otherwise we copy the old date
        if self.request.user.is_superuser:
            return models.Challenge.objects.all()
        return models.Challenge.available.all()

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        try:
            context["user_entry"] = entry = self.object.challengeentry_set.get(
                user=self.request.user
            )
            context["processes"] = entry.challengeprocess_set.filter(running=True)
            context["writeup_html"] = markdownize(entry.writeup)
        except models.ChallengeEntry.DoesNotExist:
            context["user_entry"] = None
        context["docker_host"] = settings.DOCKER_HOST
        context["description"] = markdownize(self.object.description)
        return context


class SubmitFlag(LoginRequiredMixin, View):
    def post(self, request, pk):
        challenge = get_object_or_404(models.Challenge, pk=pk)
        if not challenge.is_active:
            raise Http404
        entry, _new = models.ChallengeEntry.objects.get_or_create(
            challenge=challenge, user=request.user,
        )
        flag = request.POST.get("flag")
        return JsonResponse({"correct": entry.submit_flag(flag)})


class SubmitWriteup(LoginRequiredMixin, View):
    def post(self, request, pk):
        challenge = get_object_or_404(models.Challenge, pk=pk)
        if not challenge.is_active:
            raise Http404
        entry, _new = models.ChallengeEntry.objects.get_or_create(
            challenge=challenge, user=request.user,
        )
        writeup = request.POST.get("writeup")
        if writeup is None:
            return JsonResponse({"error": "no writeup included"}, status=400)
        entry.writeup = writeup = unescape(
            bleach.clean(
                writeup,
                attributes=bleach.sanitizer.ALLOWED_ATTRIBUTES,
                tags=bleach.sanitizer.ALLOWED_TAGS,
                strip=True,
            )
        )
        entry.save()
        return JsonResponse({"preview_html": markdownize(writeup)})


class ChallengeProcessCreateView(LoginRequiredMixin, View):
    def post(self, request, pk):
        challenge = get_object_or_404(models.Challenge, pk=pk)
        if not challenge.is_active:
            raise Http404
        entry, _new = models.ChallengeEntry.objects.get_or_create(
            challenge=challenge, user=request.user,
        )
        models.ChallengeProcess.start(entry)
        return JsonResponse({"started": True})


class ChallengeProcessStopView(LoginRequiredMixin, View):
    def post(self, request, pk):
        process = get_object_or_404(
            models.ChallengeProcess, pk=pk, challenge_entry__user=request.user
        )
        process.delete()
        return JsonResponse({"stopped": True})
