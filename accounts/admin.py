from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import CompanyProfile

# Register your models here.

class CompanyProfileInline(admin.StackedInline):
    model = CompanyProfile
    can_delete = False
    verbose_name_plural = 'Company Profile'
    fk_name = 'user'
    fieldsets = (
        ('Company Information', {
            'fields': ('company_name', 'tax_id', 'bank_account')
        }),
        ('Contact Information', {
            'fields': ('address_line1', 'address_line2', 'city', 'state', 'postal_code', 'country')
        }),
        ('Contact Details', {
            'fields': ('email', 'phone')
        }),
    )

class CustomUserAdmin(UserAdmin):
    inlines = (CompanyProfileInline, )

# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
