from django import template

register = template.Library()


@register.filter(name="replace_underscore")
def replace_underscore(value: str, replacement: str = " "):
    if not isinstance(value, str):
        return value
    return value.replace("_", replacement)
