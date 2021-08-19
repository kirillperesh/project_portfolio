from django.db import models


class OrderFiltersManager(models.Manager):
    def get_latest_current(self):
        """Returns the latest order of 'current' status"""
        return self.filter(status='CUR').order_by('-created').first()