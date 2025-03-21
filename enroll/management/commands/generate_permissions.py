from django.core.management.base import BaseCommand
from enroll.models import Permission
from enroll.permissions import SIDEBAR_PERMISSIONS

class Command(BaseCommand):
    help = 'Generate permissions based on sidebar menu items'

    def handle(self, *args, **kwargs):
        for section, permissions in SIDEBAR_PERMISSIONS.items():
            for codename in permissions:
                if not Permission.objects.filter(codename=codename).exists():
                    Permission.objects.create(codename=codename, name=f"Can {codename.replace('_', ' ')}")
                    self.stdout.write(self.style.SUCCESS(f'Permission {codename} created'))
                else:
                    self.stdout.write(self.style.WARNING(f'Permission {codename} already exists'))
