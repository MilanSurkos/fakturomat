from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class CompanyProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='company_profile')
    company_name = models.CharField(max_length=100, blank=True, verbose_name='Company Name')
    address_line1 = models.CharField(max_length=100, blank=True, verbose_name='Address Line 1')
    address_line2 = models.CharField(max_length=100, blank=True, verbose_name='Address Line 2')
    city = models.CharField(max_length=50, blank=True, verbose_name='City')
    state = models.CharField(max_length=50, blank=True, verbose_name='State/Province')
    postal_code = models.CharField(max_length=20, blank=True, verbose_name='ZIP/Postal Code')
    country = models.CharField(max_length=50, blank=True, verbose_name='Country')
    email = models.EmailField(blank=True, verbose_name='Business Email')
    phone = models.CharField(max_length=20, blank=True, verbose_name='Phone Number')
    tax_id = models.CharField(max_length=50, blank=True, verbose_name='Tax ID')
    bank_account = models.CharField(max_length=50, blank=True, verbose_name='Bank Account (IBAN)')
    
    def __str__(self):
        return f"{self.company_name}'s Profile"

@receiver(post_save, sender=User)
def create_company_profile(sender, instance, created, **kwargs):
    if created:
        CompanyProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_company_profile(sender, instance, **kwargs):
    if hasattr(instance, 'company_profile'):
        instance.company_profile.save()
