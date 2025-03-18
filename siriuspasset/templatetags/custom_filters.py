from django import template
import os

register = template.Library()

@register.filter
def basename(value):
    """Return the filename part of a file path."""
    if not value:
        return ""
    return os.path.basename(value) 