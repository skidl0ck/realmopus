from django import template

register = template.Library()


@register.filter
def humanize_action(value: str) -> str:
    """'created_lot' -> 'Created lot'"""
    if not value:
        return value
    return value.replace("_", " ").capitalize()