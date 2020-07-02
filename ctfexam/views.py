from django.http import HttpRequest, HttpResponse
from django.shortcuts import render


def index(request: HttpRequest) -> HttpResponse:
    """Render the index"""

    return render(request, "ctf/index.html")


def faq(request: HttpRequest) -> HttpResponse:
    """Render the index"""

    return render(request, "ctf/faq.html")
