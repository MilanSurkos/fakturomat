from django import forms
from decimal import Decimal
from .models import Invoice, InvoiceItem

class InvoiceForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = [
            'client', 'issue_date', 'due_date', 'status', 'payment_method',
            'currency', 'notes'
        ]
        widgets = {
            'version': forms.HiddenInput(),
        }
        
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.items_formset = kwargs.pop('items_formset', None)
        
        # Get client from initial data if provided
        initial = kwargs.get('initial', {})
        data = kwargs.get('data', {})
        
        # Try to get client from data if not in initial
        if 'client' not in initial and data and 'client' in data:
            from clients.models import Client
            try:
                client_id = data.get('client')
                if client_id:
                    client = Client.objects.get(pk=client_id)
                    initial['client'] = client
                    # Also set it in the data dict for proper form validation
                    if hasattr(data, '_mutable') and not data._mutable:
                        data = data.copy()
                        data['client'] = client_id
                        kwargs['data'] = data
            except (Client.DoesNotExist, ValueError, TypeError) as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error getting client: {e}")
        
        kwargs['initial'] = initial
        super().__init__(*args, **kwargs)
        
        # Set default values
        self.fields['status'].initial = 'draft'
        self.fields['payment_method'].initial = 'bank_transfer'
        self.fields['currency'].initial = 'EUR'
        
        # Make client field required and set attributes
        self.fields['client'].required = True
        self.fields['client'].widget.attrs.update({
            'required': 'required',
            'class': 'form-select',
            'aria-label': 'Select client'
        })
        
        # Set default issue_date to today if not already set
        if 'issue_date' not in self.initial and not self.instance.pk:
            from django.utils import timezone
            self.fields['issue_date'].initial = timezone.now().date()
        
        # Ensure payment method choices are properly set
        self.fields['payment_method'].choices = [('', 'Select a payment method')] + [
            (choice[0], choice[1]) for choice in self.Meta.model.PAYMENT_METHODS
        ]
        
        # Add Bootstrap classes to form fields
        for field_name, field in self.fields.items():
            if field_name == 'payment_method':
                field.widget.attrs.update({
                    'class': 'form-select',
                    'required': 'required',
                    'aria-label': 'Payment method'
                })
            else:
                field.widget.attrs['class'] = 'form-control'
                
            # Add is-invalid class if field has errors
            if field_name in self.errors:
                field.widget.attrs['class'] += ' is-invalid'
            
        # Set input type to date for date fields
        self.fields['issue_date'].widget = forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
        self.fields['due_date'].widget = forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
        
        # Handle version field if it exists in the form
        if 'version' in self.fields and self.instance and hasattr(self.instance, 'version'):
            self.fields['version'].initial = self.instance.version
        
        # Set date format for display
        self.fields['issue_date'].widget.format = '%Y-%m-%d'
        self.fields['due_date'].widget.format = '%Y-%m-%d'
        
    def clean(self):
        import logging
        logger = logging.getLogger(__name__)
        logger.info("\n=== Form Clean Method Started ===")
        
        cleaned_data = super().clean()
        logger.info(f"[form:clean] Form cleaned data: {cleaned_data}")
        
        client = cleaned_data.get('client')
        issue_date = cleaned_data.get('issue_date')
        due_date = cleaned_data.get('due_date')
        
        # Log all form fields and their values for debugging
        logger.info("[form:clean] Form fields and values:")
        for field_name, value in cleaned_data.items():
            logger.info(f"  {field_name}: {value} ({type(value)})")
        
        # Client validation
        if not client:
            error_msg = "A client must be selected."
            logger.warning(f"[form:clean] {error_msg}")
            self.add_error('client', error_msg)
        else:
            logger.info(f"[form:clean] Client selected: {client.id} - {client.name}")
            
            # Ensure the client belongs to the current user (if user is not admin)
            user = getattr(self, 'user', None)
            logger.info(f"[form:clean] Current user: {user}")
            
            if user and not user.is_superuser and hasattr(user, 'client'):
                logger.info(f"[form:clean] Checking client permissions for user {user.id}")
                if client not in user.client.clients.all():
                    error_msg = "You don't have permission to create an invoice for this client."
                    logger.warning(f"[form:clean] {error_msg}")
                    self.add_error('client', error_msg)
        
        # Date validation
        if issue_date and due_date and due_date < issue_date:
            error_msg = 'Due date cannot be before the issue date.'
            logger.warning(f"[form:clean] {error_msg}")
            self.add_error('due_date', error_msg)
        
        # Formset validation - only if we have a formset
        if hasattr(self, 'items_formset') and self.items_formset is not None:
            items_formset = self.items_formset
            
            # Log formset data for debugging
            logger.info("[form:clean] Formset data:")
            for i, form in enumerate(items_formset.forms):
                logger.info(f"  Form {i} data: {form.data if hasattr(form, 'data') else 'No data'}")
                logger.info(f"  Form {i} cleaned_data: {getattr(form, 'cleaned_data', {})}")
            
            # Check if formset is valid
            if not items_formset.is_valid():
                logger.warning("[form:clean] Formset is not valid")
                for i, form in enumerate(items_formset.forms):
                    if form.errors:
                        logger.warning(f"[form:clean] Form {i} errors: {form.errors}")
                        for field, errors in form.errors.items():
                            for error in errors:
                                self.add_error(None, f"Item {i+1}, {form.fields[field].label}: {error}")
                
                # Also add non-form errors
                for error in items_formset.non_form_errors():
                    self.add_error(None, error)
            
            # Check for at least one valid item and validate each item
            has_valid_forms = False
            for i, form in enumerate(items_formset.forms):
                if form.cleaned_data.get('DELETE', False):
                    continue
                    
                # Check if form has any data
                has_data = any(
                    field for field in form.cleaned_data.values() 
                    if field not in (None, '', 0, '0', 0.0, '0.0')
                )
                
                if has_data:
                    # Validate required fields for items with data
                    if not form.cleaned_data.get('description'):
                        form.add_error('description', 'This field is required.')
                    if form.cleaned_data.get('quantity') is None or form.cleaned_data.get('quantity') <= 0:
                        form.add_error('quantity', 'Quantity must be greater than 0.')
                    if form.cleaned_data.get('unit_price') is None or form.cleaned_data.get('unit_price') < 0:
                        form.add_error('unit_price', 'Unit price must be a positive number.')
                    
                    # Only consider the form valid if it has no errors
                    if not form.errors:
                        has_valid_forms = True
            
            if not has_valid_forms:
                error_msg = 'At least one valid invoice item is required.'
                logger.warning(f"[form:clean] {error_msg}")
                self.add_error(None, error_msg)
            
            # Store the formset for later use
            self.valid_forms = [f for f in items_formset.forms if not f.cleaned_data.get('DELETE', False) and 
                              any(v not in (None, '', 0, '0', 0.0, '0.0') 
                                  for k, v in f.cleaned_data.items() 
                                  if k != 'id')]
        else:
            logger.warning("[form:clean] No items_formset found in form")
            
            # If this is a POST request and we don't have a formset, that's an error
            if hasattr(self, 'data') and self.data:
                error_msg = 'Invalid form data. Please try again.'
                logger.error(f"[form:clean] {error_msg}")
                self.add_error(None, error_msg)
        
        logger.info(f"[form:clean] Form errors after clean: {self.errors}")
        return cleaned_data
    
    def save(self, commit=True):
        import logging
        from django.db import transaction
        logger = logging.getLogger(__name__)
        
        logger = logging.getLogger(__name__)
        logger.info("=== InvoiceForm.save() called ===")
        logger.info(f"Commit: {commit}")
        
        # Get the instance but don't save it yet
        instance = super().save(commit=False)
        
        # Ensure client is set from form data if not already set
        if not instance.client and 'client' in self.cleaned_data and self.cleaned_data['client']:
            instance.client = self.cleaned_data['client']
            logger.info(f"Set client to: {instance.client.id}")
        
        # Set the created_by field if this is a new instance
        if not instance.pk and hasattr(self, 'user'):
            instance.created_by = self.user
            logger.info(f"Set created_by to user: {self.user.id}")
        
        if not commit:
            logger.info("Not committing, returning instance without saving")
            return instance
        
        try:
            with transaction.atomic():
                logger.info("Starting database transaction...")
                
                # Save the invoice first to get an ID
                instance.save()
                logger.info(f"Invoice saved with ID: {instance.id}")
                
                # Save the formset if it exists
                if hasattr(self, 'items_formset') and self.items_formset is not None:
                    logger.info("Saving items formset...")
                    
                    # Set the instance on the formset
                    self.items_formset.instance = instance
                    
                    # Save the formset
                    items = self.items_formset.save(commit=False)
                    
                    # Delete any items marked for deletion
                    for obj in self.items_formset.deleted_objects:
                        obj.delete()
                    
                    # Save the new items
                    for item in items:
                        # Skip items that are missing required fields
                        if not item.description or item.quantity is None or item.unit_price is None:
                            logger.warning(f"Skipping invalid item: {item}")
                            continue
                            
                        item.invoice = instance
                        item.save()
                        logger.info(f"Saved invoice item: {item.description}")
                    
                    logger.info(f"Saved {len(items)} invoice items")
                    
                    # Update totals after saving all items
                    logger.info("Updating invoice totals...")
                    totals = instance.update_totals(save=True)
                    logger.info(f"Invoice totals updated: {totals}")
                
                # Log the final state of the invoice
                logger.info(f"Final invoice state - Subtotal: {instance.subtotal}, Tax: {instance.tax_amount}, Total: {instance.total_amount}")
                
                # Refresh the instance to ensure we have the latest data
                instance.refresh_from_db()
                logger.info(f"Refreshed instance - Subtotal: {instance.subtotal}, Tax: {instance.tax_amount}, Total: {instance.total_amount}")
                
                return instance
                
        except Exception as e:
            logger.error(f"Error saving invoice: {str(e)}")
            logger.exception("Exception details:")
            raise


class InvoiceItemForm(forms.ModelForm):
    class Meta:
        model = InvoiceItem
        fields = ['description', 'quantity', 'unit_price']
        widgets = {
            'description': forms.TextInput(attrs={
                'class': 'form-control',
                'required': 'required',
                'placeholder': 'Item description'
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'required': 'required',
                'min': '1',
                'step': '1',
                'placeholder': '1'
            }),
            'unit_price': forms.NumberInput(attrs={
                'class': 'form-control',
                'required': 'required',
                'min': '0',
                'step': '0.01',
                'placeholder': '0.00'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Make fields not required by default
        for field in self.fields.values():
            field.required = False
            
        # Add VAT rate as a hidden field with fixed value
        self.fields['vat_rate'] = forms.DecimalField(
            initial=InvoiceItem.VAT_RATE,
            widget=forms.HiddenInput(attrs={
                'min': '0',
                'max': '100',
                'step': '0.01',
                'aria-label': 'VAT rate'
            }),
            required=False
        )
        
        # Set initial VAT rate to the fixed value from the model
        self.initial['vat_rate'] = InvoiceItem.VAT_RATE

    def clean(self):
        cleaned_data = super().clean()

        # Check if this is a form submission or just initial page load
        is_submitted = hasattr(self, 'data') and self.data

        # Get values from cleaned_data
        description = cleaned_data.get('description', '')
        if description is not None:
            description = str(description).strip()
        quantity = cleaned_data.get('quantity')
        unit_price = cleaned_data.get('unit_price')
        vat_rate = cleaned_data.get('vat_rate', 0)

        # Check if this is an empty form (all fields empty or deleted)
        is_empty = not any([description, quantity is not None, unit_price is not None])

        # If the form is empty and not marked for deletion, skip validation
        if is_empty and not cleaned_data.get('DELETE', False):
            # Skip validation for empty forms that aren't being deleted
            return cleaned_data

        # If we're here, either the form has data or is being deleted

        # If the form is being deleted, skip further validation
        if cleaned_data.get('DELETE', False):
            return cleaned_data
            
        # If we have a description but missing quantity or unit_price, raise validation error
        if description and (quantity is None or unit_price is None):
            if quantity is None:
                self.add_error('quantity', 'This field is required.')
            if unit_price is None:
                self.add_error('unit_price', 'This field is required.')
            return cleaned_data

        # If we get here, the form has data and is not being deleted

        # Only validate if this is a form submission
        if is_submitted:
            # Ensure quantity is provided and positive
            if quantity is None:
                self.add_error('quantity', 'Quantity is required')
            elif quantity <= 0:
                self.add_error('quantity', 'Quantity must be greater than zero')
                
            # Ensure unit price is provided and not negative
            if unit_price is None:
                self.add_error('unit_price', 'Unit price is required')
            elif unit_price < 0:
                self.add_error('unit_price', 'Unit price cannot be negative')
                
            # Only calculate total if both fields are valid and provided
            if not self.errors and quantity is not None and unit_price is not None:
                try:
                    # Convert to Decimal for precise calculations
                    from decimal import Decimal
                    quantity_decimal = Decimal(str(quantity))
                    unit_price_decimal = Decimal(str(unit_price))
                    vat_rate_decimal = Decimal(str(vat_rate)) if vat_rate is not None else Decimal('0')
                    
                    # Calculate totals
                    subtotal = quantity_decimal * unit_price_decimal
                    tax_amount = subtotal * (vat_rate_decimal / Decimal('100'))
                    total = subtotal + tax_amount
                    
                    # Update cleaned data with calculated values
                    cleaned_data['subtotal'] = subtotal.quantize(Decimal('0.01'))
                    cleaned_data['tax_amount'] = tax_amount.quantize(Decimal('0.01'))
                    cleaned_data['total'] = total.quantize(Decimal('0.01'))
                    
                except (TypeError, ValueError, decimal.InvalidOperation) as e:
                    self.add_error(None, f'Error calculating totals: {str(e)}')
        
        return cleaned_data

# Formset for invoice items
class BaseInvoiceItemFormSet(forms.BaseInlineFormSet):
    def __init__(self, *args, **kwargs):
        # Remove 'extra' from kwargs if it exists to prevent passing it to parent
        extra = kwargs.pop('extra', None)
        super().__init__(*args, **kwargs)
        # Ensure at least one form is displayed
        self.min_num = 1
        self.validate_min = True
        
        # Set extra forms if provided
        if extra is not None:
            self.extra = extra
        
    def clean(self):
        """
        Custom clean method to calculate and validate invoice totals
        """
        super().clean()
        
        # Skip validation if there are already errors
        if self._non_form_errors:
            return
            
        # Check if we have at least one valid non-deleted form
        valid_forms = []
        for form in self.forms:
            if form.cleaned_data.get('DELETE', False):
                continue
                
            # Check if this form has the required fields
            has_description = bool(form.cleaned_data.get('description', '').strip())
            has_quantity = form.cleaned_data.get('quantity') is not None
            has_unit_price = form.cleaned_data.get('unit_price') is not None
            
            # If any field is present, we consider it a form with data
            if has_description or has_quantity or has_unit_price:
                # If any required field is missing, mark it as an error
                if not has_description:
                    form.add_error('description', 'This field is required.')
                if not has_quantity:
                    form.add_error('quantity', 'This field is required.')
                if not has_unit_price:
                    form.add_error('unit_price', 'This field is required.')
                
                # Only add to valid_forms if all required fields are present and valid
                if has_description and has_quantity and has_unit_price and not form.errors:
                    valid_forms.append(form)
        
        # If no valid forms, raise validation error
        if not valid_forms and any(not form.cleaned_data.get('DELETE', False) for form in self.forms):
            raise forms.ValidationError(
                'At least one valid item is required.',
                code='missing_items'
            )
            
        # Calculate totals from valid forms
        subtotal = Decimal('0.00')
        tax_amount = Decimal('0.00')
        total = Decimal('0.00')
        
        for form in valid_forms:
            if form.cleaned_data.get('DELETE', False):
                continue
                
            # Get values from form's cleaned_data
            quantity = form.cleaned_data.get('quantity', Decimal('0'))
            unit_price = form.cleaned_data.get('unit_price', Decimal('0'))
            vat_rate = form.cleaned_data.get('vat_rate')
            # Ensure vat_rate is not None and is a Decimal
            if vat_rate is None:
                vat_rate = Decimal('0')
            
            # Calculate item totals
            item_subtotal = quantity * unit_price
            item_tax = item_subtotal * (vat_rate / Decimal('100'))
            item_total = item_subtotal + item_tax
            
            # Update running totals
            subtotal += item_subtotal
            tax_amount += item_tax
            total += item_total
            
            # Update the form's cleaned data with calculated values
            form.cleaned_data['subtotal'] = item_subtotal.quantize(Decimal('0.01'))
            form.cleaned_data['tax_amount'] = item_tax.quantize(Decimal('0.01'))
            form.cleaned_data['total'] = item_total.quantize(Decimal('0.01'))
        
        # Store calculated totals in the formset for template use
        self.subtotal = subtotal.quantize(Decimal('0.01'))
        self.tax_amount = tax_amount.quantize(Decimal('0.01'))
        self.total_amount = total.quantize(Decimal('0.01'))
        
        # Store in the form's data so it gets saved with the form
        if hasattr(self, 'instance') and self.instance:
            self.instance.subtotal = self.subtotal
            self.instance.tax_amount = self.tax_amount
            self.instance.total_amount = self.total_amount

InvoiceItemFormSet = forms.inlineformset_factory(
    Invoice,
    InvoiceItem,
    form=InvoiceItemForm,
    formset=BaseInvoiceItemFormSet,
    extra=1,  # Start with 1 empty form
    can_delete=True,
    min_num=1,  # Require at least 1 form
    validate_min=True
)
