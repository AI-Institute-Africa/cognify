"""
folder_perms – Template tag library for Institutional Folder permissions.

Usage in templates:
    {% load folder_perms %}

    {% if request.user|can_create_folder %}
        <button>New Folder</button>
    {% endif %}

    {% if request.user|can_delete_folder %}
        <button>Delete</button>
    {% endif %}

    {% if request.user|can_download_folder %}
        <button>Download</button>
    {% endif %}
"""

from django import template
from registry.models import InstitutionalFolderPermission

register = template.Library()


def _user_can(user, perm: str) -> bool:
    if not user or not user.is_authenticated:
        return False
    return InstitutionalFolderPermission.user_can(user, perm)


@register.filter(name='can_create_folder')
def can_create_folder(user):
    """Return True if the user may create Cloud Vault folders."""
    return _user_can(user, 'can_create_folder')


@register.filter(name='can_delete_folder')
def can_delete_folder(user):
    """Return True if the user may delete Cloud Vault folders."""
    return _user_can(user, 'can_delete_folder')


@register.filter(name='can_download_folder')
def can_download_folder(user):
    """Return True if the user may download Cloud Vault folder contents as ZIP."""
    return _user_can(user, 'can_download_folder')


@register.filter(name='can_view_all_folders')
def can_view_all_folders(user):
    """Return True if the user may view folders from all departments."""
    return _user_can(user, 'can_view_all_folders')


@register.filter(name='replace_underscores')
def replace_underscores(value):
    """Replace underscores with spaces and title-case the result."""
    if value is None:
        return '—'
    return str(value).replace('_', ' ').title()


@register.filter(name='safe_name')
def safe_name(user, fallback='Not assigned'):
    """
    Safely return a display name for a nullable user FK.

    Usage:  {{ req.dept_manager|safe_name }}
            {{ req.dept_manager|safe_name:"—" }}

    Unlike  {{ user.get_full_name|default:user.username }}  this filter
    never raises VariableDoesNotExist when the FK is None.
    """
    if user is None:
        return fallback
    full = ''
    try:
        full = user.get_full_name()
    except Exception:
        pass
    return full or getattr(user, 'username', '') or fallback

