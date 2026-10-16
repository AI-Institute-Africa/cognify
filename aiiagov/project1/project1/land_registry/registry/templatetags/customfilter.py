from django import template
from cryptography.fernet import Fernet
from django.conf import settings
import os


register = template.Library()

@register.filter
def replaceBlank(value,stringVal = ""):
    value = str(value).replace(stringVal, '')
    return value

@register.filter
def encryptdata(value):
    fernet = Fernet(settings.ID_ENCRYPTION_KEY)
    value = fernet.encrypt(str(value).encode())
    return value

@register.filter
def subtract(value, arg):
    try:
        return float(value) - float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def multiply(value, arg):
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def divide(value, arg):
    try:
        return float(value) / float(arg) if float(arg) != 0 else 0
    except (ValueError, TypeError):
        return 0

@register.filter
def is_selected(value, arg):
    return str(value) == str(arg)

@register.filter
def filter_status_count(queryset, status):
    try:
        # If it's a list (already evaluated)
        return len([obj for obj in queryset if obj.status == status])
    except:
        return 0

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)

@register.filter
def split(value, arg):
    return value.split(arg)

@register.filter
def basename(value):
    return os.path.basename(value)

@register.filter
def width_style(value):
    try:
        # Round to 1 decimal place to prevent excessively long strings
        w = round(float(value), 1)
        return f"width: {w}%"
    except (ValueError, TypeError):
        return "width: 0%"
