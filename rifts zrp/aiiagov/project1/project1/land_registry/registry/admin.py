from django.contrib import admin
from django.apps import apps
from django.utils.html import format_html

# ── Institutional Folder Permission Admin ─────────────────────────────────────

from registry.models import InstitutionalFolderPermission


@admin.register(InstitutionalFolderPermission)
class InstitutionalFolderPermissionAdmin(admin.ModelAdmin):
    """
    Admin panel for managing per-user Cloud Vault (Institutional Folder)
    permissions.  Only superusers can access this section.
    """

    list_display   = (
        'user_display',
        'can_view_all_folders',
        'can_create_folder',
        'can_delete_folder',
        'can_download_folder',
        'granted_by',
        'granted_at',
        'notes_short',
    )
    list_filter    = ('can_view_all_folders', 'can_create_folder', 'can_delete_folder', 'can_download_folder')
    search_fields  = ('user__username', 'user__first_name', 'user__last_name', 'user__email')
    readonly_fields = ('granted_by', 'granted_at')
    ordering       = ('user__username',)

    fieldsets = (
        ('User', {
            'fields': ('user',),
        }),
        ('Permissions', {
            'description': (
                'Grant the permissions this user may exercise on Institutional Folders '
                'in the Cloud Vault.  Superusers always have all permissions regardless '
                'of these settings.'
            ),
            'fields': (
                'can_view_all_folders',
                'can_create_folder',
                'can_delete_folder',
                'can_download_folder',
            ),
        }),
        ('Audit', {
            'fields': ('granted_by', 'granted_at', 'notes'),
            'classes': ('collapse',),
        }),
    )

    # ── Helpers ───────────────────────────────────────────────────────────────

    @admin.display(description='User')
    def user_display(self, obj):
        full = obj.user.get_full_name()
        return format_html(
            '<strong>{}</strong><br><small style="color:#999">{}</small>',
            full or obj.user.username,
            obj.user.email or '—',
        )

    @admin.display(description='Notes')
    def notes_short(self, obj):
        return obj.notes[:60] + '…' if len(obj.notes) > 60 else (obj.notes or '—')

    def save_model(self, request, obj, form, change):
        """Auto-record which admin granted the permissions."""
        obj.granted_by = request.user
        super().save_model(request, obj, form, change)

    def has_module_perms(self, request):
        return request.user.is_superuser

    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


# ── Auto-register remaining models ───────────────────────────────────────────
# All models not explicitly registered above are auto-registered so that they
# appear in admin with a basic list view.

already_registered = {InstitutionalFolderPermission}
app_models = apps.get_app_config('registry').get_models()

for model in app_models:
    if model in already_registered:
        continue
    try:
        admin.site.register(model)
    except admin.sites.AlreadyRegistered:
        pass
