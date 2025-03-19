from django import template
import os

register = template.Library()

@register.filter
def basename(value):
    """Return the filename part of a file path."""
    if not value:
        return ""
    return os.path.basename(value) 

@register.filter
def get_range(value):
    """Return a range of numbers from 0 to value-1."""
    return range(value)

@register.filter
def get_by_index(sequence, index):
    """Return the item at the given index in the sequence."""
    try:
        return sequence[index]
    except (IndexError, TypeError):
        return None

@register.filter
def add(value, arg):
    """Add the arg to the value."""
    try:
        return int(value) + int(arg)
    except (ValueError, TypeError):
        return value 