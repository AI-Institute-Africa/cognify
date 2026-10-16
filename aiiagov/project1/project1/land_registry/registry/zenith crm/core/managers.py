from django.db import models


class ActiveQuerySet(models.QuerySet):
    def active(self):
        return self.filter(is_active=True, is_deleted=False)

    def deleted(self):
        return self.filter(is_deleted=True)

    def hard_delete(self):
        return super().delete()


class SoftDeleteManager(models.Manager):
    def get_queryset(self):
        return ActiveQuerySet(self.model, using=self._db).filter(is_deleted=False)

    def all_with_deleted(self):
        return ActiveQuerySet(self.model, using=self._db)

    def deleted(self):
        return self.all_with_deleted().deleted()
