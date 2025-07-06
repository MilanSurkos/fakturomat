from django import forms
from django.forms import ModelForm
from .models import Client, ClientNote


class ClientForm(ModelForm):
    class Meta:
        model = Client
        fields = [
            'type', 'name', 'email', 'phone', 'mobile',
            'tax_number', 'vat_number', 'address', 'city',
            'state', 'postal_code', 'country', 'website', 
            'account_number', 'iban', 'bic_swift', 'bank_name',
            'notes'
        ]
        widgets = {
            'type': forms.Select(attrs={
                'class': 'form-select',
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Full name or company name'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'client@example.com'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+386 1 234 5678'
            }),
            'mobile': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+386 41 234 567'
            }),
            'tax_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Tax identification number'
            }),
            'vat_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'VAT identification number (SIXXXXXXXX)'
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2
            }),
            'city': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'City'
            }),
            'state': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'State/Province/Region'
            }),
            'postal_code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Postal code'
            }),
            'country': forms.Select(attrs={
                'class': 'form-select',
            }),
            'website': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://example.com'
            }),
            'account_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Account Number'
            }),
            'iban': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'IBAN (e.g., SI56 1234 1234 1234 123)'
            }),
            'bic_swift': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'BIC/SWIFT code'
            }),
            'bank_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Name of the bank'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Any additional notes about this client...'
            }),
        }
        labels = {
            'type': 'Client Type',
            'vat_number': 'VAT Number',
            'tax_number': 'Tax Number',
            'postal_code': 'Postal Code',
            'account_number': 'Account Number',
            'bic_swift': 'BIC/SWIFT Code',
            'bank_name': 'Bank Name',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add form-control class to all fields
        for field in self.fields.values():
            if 'class' not in field.widget.attrs:
                field.widget.attrs['class'] = 'form-control'


class ClientNoteForm(ModelForm):
    class Meta:
        model = ClientNote
        fields = ['note']
        widgets = {
            'note': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Add a note about this client...'
            }),
        }


class ClientFilterForm(forms.Form):
    CLIENT_TYPE_CHOICES = [
        ('', 'All Types'),
        ('individual', 'Individual'),
        ('company', 'Company'),
    ]
    
    q = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search clients...',
            'autocomplete': 'off',
        }),
        label=''
    )
    
    client_type = forms.ChoiceField(
        choices=CLIENT_TYPE_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select',
        })
    )
    
    sort_by = forms.ChoiceField(
        choices=[
            ('name', 'Name (A-Z)'),
            ('-name', 'Name (Z-A)'),
            ('created_at', 'Oldest First'),
            ('-created_at', 'Newest First'),
        ],
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select',
        })
    )
    
    def filter_queryset(self, queryset):
        data = self.cleaned_data
        
        # Apply search query
        if data.get('q'):
            queryset = queryset.filter(
                models.Q(name__icontains=data['q']) |
                models.Q(email__icontains=data['q']) |
                models.Q(phone__icontains=data['q']) |
                models.Q(tax_number__icontains=data['q']) |
                models.Q(vat_number__icontains=data['q'])
            )
        
        # Filter by client type
        if data.get('client_type'):
            queryset = queryset.filter(type=data['client_type'])
        
        # Apply sorting
        if data.get('sort_by'):
            queryset = queryset.order_by(data['sort_by'])
        
        return queryset
