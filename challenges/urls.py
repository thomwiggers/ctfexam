from django.urls import path

from . import views

app_name = "challenges"

urlpatterns = [
    path("", views.ChallengeListView.as_view(), name="challenges"),
    path("<int:pk>/", views.ChallengeDetailView.as_view(), name="challenge"),
    path("<int:pk>/submit_flag", views.SubmitFlag.as_view(), name="submit_flag"),
    path(
        "<int:pk>/submit_writeup", views.SubmitWriteup.as_view(), name="submit_writeup"
    ),
    path(
        "process/new/challenge/<int:pk>/",
        views.ChallengeProcessCreateView.as_view(),
        name="create_process",
    ),
    path(
        "process/delete/<int:pk>/",
        views.ChallengeProcessStopView.as_view(),
        name="delete-process",
    ),
]
