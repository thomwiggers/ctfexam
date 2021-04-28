from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.conf import settings


def index(request: HttpRequest) -> HttpResponse:
    """Render the index"""

    return render(
        request,
        "ctf/index.html",
        {"disclaimer": settings.SHOW_DISCLAIMER, "example": settings.SHOW_EXAMPLE},
    )


def faq(request: HttpRequest) -> HttpResponse:
    """Render the index"""

    return render(request, "ctf/faq.html")
