from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from accounts.models import CompanyProfile

class Command(BaseCommand):
    help = 'Check if CompanyProfile exists for users'

    def handle(self, *args, **options):
        User = get_user_model()
        for user in User.objects.all():
            try:
                profile = CompanyProfile.objects.get(user=user)
                self.stdout.write(self.style.SUCCESS(f'CompanyProfile exists for user: {user.username}'))
                self.stdout.write(f'Company Name: {profile.company_name}')
            except CompanyProfile.DoesNotExist:
                self.stdout.write(self.style.WARNING(f'No CompanyProfile for user: {user.username}'))
                # Create one if it doesn't exist
                profile = CompanyProfile.objects.create(user=user)
                self.stdout.write(self.style.SUCCESS(f'Created CompanyProfile for user: {user.username}'))
