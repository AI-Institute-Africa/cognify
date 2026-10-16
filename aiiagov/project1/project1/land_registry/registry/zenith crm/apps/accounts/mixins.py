from django.contrib.auth.mixins import AccessMixin


class GroupRequiredMixin(AccessMixin):
    group_required = None

    def get_group_required(self):
        if self.group_required is None:
            return []
        if isinstance(self.group_required, (list, tuple)):
            return self.group_required
        return [self.group_required]

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        required_groups = self.get_group_required()
        if required_groups and not request.user.groups.filter(name__in=required_groups).exists() and not request.user.is_superuser:
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)
