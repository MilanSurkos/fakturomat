from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth.models import User
from django_countries.fields import CountryField

class Client(models.Model):
    CLIENT_TYPES = (
        ('individual', 'Individual'),
        ('company', 'Company'),
    )
    
    type = models.CharField(max_length=10, choices=CLIENT_TYPES, default='individual')
    name = models.CharField(max_length=200)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    mobile = models.CharField(max_length=20, blank=True, null=True)
    tax_number = models.CharField('Tax Number', max_length=50, blank=True, null=True)
    vat_number = models.CharField('VAT Number', max_length=50, blank=True, null=True)
    
    # Address
    address = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    postal_code = models.CharField(max_length=20, blank=True, null=True)
    country = CountryField(default='SK')
    
    # Additional Info
    website = models.URLField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    
    # Payment Information
    account_number = models.CharField('Account Number', max_length=50, blank=True, null=True)
    iban = models.CharField('IBAN', max_length=50, blank=True, null=True)
    bic_swift = models.CharField('BIC/SWIFT', max_length=20, blank=True, null=True)
    bank_name = models.CharField('Bank Name', max_length=100, blank=True, null=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='clients_created')
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='clients_updated')
    
    class Meta:
        ordering = ['name']
        verbose_name = 'Client'
        verbose_name_plural = 'Clients'
    
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('clients:detail', kwargs={'pk': self.pk})
    
    def get_full_address(self):
        address_parts = []
        if self.address:
            address_parts.append(self.address)
        if self.postal_code or self.city:
            address_parts.append(f"{self.postal_code or ''} {self.city or ''}".strip())
        if self.state:
            address_parts.append(self.state)
        if self.country and self.country != 'Slovenia':
            address_parts.append(self.country)
        return ', '.join(address_parts)


class ClientNote(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='client_notes')
    note = models.TextField()
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Client Note'
        verbose_name_plural = 'Client Notes'
    
    def __str__(self):
        return f"Note for {self.client.name} by {self.created_by}"
