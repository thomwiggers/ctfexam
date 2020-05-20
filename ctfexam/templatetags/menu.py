"""Provides the main menu by generating it from a dict"""

from django import template
from django.urls import reverse
from typing import List, Dict


MAIN_MENU: List[Dict[str, str]] = [
    {
        'title': "Home",
        'name': 'index',
    },
    {
        "title": "Challenges",
        'name': 'challenges:challenges',
    },
]

register = template.Library()


@register.inclusion_tag("menu.html", takes_context=True)
def render_main_menu(context: Dict):
    """Renders the main menu in this place"""

    path = None
    if "request" in context:
        path = context['request'].path

    for item in MAIN_MENU:
        item['url'] = reverse(item["name"])
        item['active'] = "name" in item and item['url'] == path

    return {"menu": MAIN_MENU, "request": context.get("request")}
