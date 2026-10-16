from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User


@receiver(post_save, sender=User)
def handle_user_created(sender, instance, created, **kwargs):
    if created:
        # Placeholder for future onboarding, audit, or role assignment logic
        pass
