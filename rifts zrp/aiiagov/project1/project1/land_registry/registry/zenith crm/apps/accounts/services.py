from django.contrib.auth.models import Group
from django.db import transaction

from .constants import DEFAULT_ROLES


class AccountService:
    @staticmethod
    @transaction.atomic
    def initialize_roles():
        groups = []
        for role in DEFAULT_ROLES:
            group, created = Group.objects.get_or_create(name=role)
            groups.append(group)
        return groups

    @staticmethod
    def assign_role(user, role_name):
        group, _ = Group.objects.get_or_create(name=role_name)
        user.groups.add(group)
        return user
