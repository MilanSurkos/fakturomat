import uuid
from decimal import Decimal, ROUND_HALF_UP
from django.db import models, transaction
from django.utils import timezone
from django.urls import reverse
from django.db.models import F, Q, Index
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.core.exceptions import ValidationError
from clients.models import Client
import json

def quantize_money(value):
    """Helper function to consistently quantize monetary values."""
    if value is None:
        return None
    return Decimal(value).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

class Invoice(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('paid', 'Paid'),
        ('overdue', 'Overdue'),
        ('pending', 'Pending'),
        ('cancelled', 'Cancelled'),
    ]
    
    PAYMENT_METHODS = [
        ('bank_transfer', 'Bank Transfer'),
        ('credit_card', 'Credit Card'),
        ('paypal', 'PayPal'),
        ('pay_by_square', 'Pay by Square'),
    ]
    
    CURRENCIES = [
        ('EUR', 'EUR (€)'),
        ('USD', 'USD ($)'),
        ('CZK', 'CZK (Kč)'),
    ]
    
    invoice_number = models.CharField(max_length=50, unique=True, blank=True, db_index=True)
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='invoices')
    issue_date = models.DateField(default=timezone.now)
    due_date = models.DateField(db_index=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', db_index=True)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='bank_transfer')
    currency = models.CharField(max_length=3, choices=CURRENCIES, default='EUR')
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0, editable=False)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, editable=False)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, editable=False)
    tax_breakdown = models.JSONField(default=dict, editable=False, help_text="Stores tax breakdown by rate")
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, related_name='invoices_created')
    version = models.UUIDField(default=uuid.uuid4, editable=False, help_text="Used for optimistic locking")
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = _('Invoice')
        verbose_name_plural = _('Invoices')
        indexes = [
            models.Index(fields=['invoice_number'], name='invoice_number_idx'),
            models.Index(fields=['status'], name='status_idx'),
            models.Index(fields=['due_date'], name='due_date_idx'),
            models.Index(fields=['client'], name='invoice_client_idx'),
            models.Index(fields=['created_at'], name='created_at_idx'),
        ]
    
    def __str__(self):
        try:
            if hasattr(self, 'client') and self.client is not None:
                return f"Invoice #{self.invoice_number or 'Draft'} - {self.client.name}"
            return f"Invoice #{self.invoice_number or 'Draft'} - No Client"
        except Exception:
            return f"Invoice #{self.invoice_number or 'Draft'} - Client Not Available"
    
    def get_absolute_url(self):
        return reverse('invoices:detail', kwargs={'pk': self.pk})
    
    def get_status_badge(self):
        """Return Bootstrap badge class based on status"""
        status_classes = {
            'draft': 'secondary',
            'sent': 'info',
            'paid': 'success',
            'overdue': 'danger',
            'pending': 'warning',
            'cancelled': 'dark',
        }
        return status_classes.get(self.status, 'secondary')
    
    def update_totals(self, save=True):
        """Update subtotal, tax, and total based on line items with proper tax handling.
        
        This method calculates:
        1. Subtotal (sum of all line item totals before tax)
        2. Tax breakdown by VAT rate
        3. Total tax amount
        4. Grand total
        
        Args:
            save (bool): If True, saves the instance after updating totals.
            
        Returns:
            dict: Dictionary containing the calculated values
        """
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"[update_totals] Starting update_totals for invoice {self.id or 'new'}")
        
        from collections import defaultdict
        
        # Initialize totals
        subtotal = Decimal('0.00')
        tax_amount = Decimal('0.00')
        tax_breakdown = defaultdict(Decimal)
        
        # Get all non-deleted items
        items = self.items.filter(deleted=False)
        logger.info(f"[update_totals] Found {items.count()} non-deleted items")
        
        # Calculate line item totals and group by VAT rate
        for idx, item in enumerate(items, 1):
            logger.info(f"[update_totals] Processing item {idx}: {item.description}")
            line_totals = item.get_line_totals()
            logger.info(f"[update_totals] Line {idx} totals: {line_totals}")
            
            # Add to subtotal (before tax)
            subtotal += line_totals['subtotal']
            
            # Add to tax breakdown using VAT rate
            tax_breakdown[str(item.vat_rate)] = float(line_totals['tax_amount'])
            tax_amount += line_totals['tax_amount']
            
            logger.info(f"[update_totals] After item {idx} - Subtotal: {subtotal}, Tax: {tax_amount}")
        
        # Update instance fields with quantized values
        self.subtotal = quantize_money(subtotal)
        self.tax_amount = quantize_money(tax_amount)
        self.total_amount = quantize_money(subtotal + tax_amount)
        self.tax_breakdown = dict(tax_breakdown)
        
        logger.info(f"[update_totals] Final values - Subtotal: {self.subtotal}, Tax: {self.tax_amount}, Total: {self.total_amount}")
        logger.info(f"[update_totals] Tax breakdown: {self.tax_breakdown}")
        
        if save:
            update_fields = [
                'subtotal', 
                'tax_amount', 
                'total_amount',
                'tax_breakdown',
                'updated_at',
                'version'  # Update version to handle concurrent updates
            ]
            logger.info("[update_totals] Saving invoice with update_fields: %s", update_fields)
            try:
                self.save(update_fields=update_fields)
                logger.info("[update_totals] Invoice saved successfully")
            except Exception as e:
                logger.error(f"[update_totals] Error saving invoice: {str(e)}")
                raise
        
        result = {
            'subtotal': self.subtotal,
            'tax_amount': self.tax_amount,
            'total_amount': self.total_amount,
            'tax_breakdown': self.tax_breakdown
        }
        
        logger.info(f"[update_totals] Returning result: {result}")
        return result
    
    def clean(self):
        """Validate the invoice data."""
        super().clean()
        
        if self.due_date and self.issue_date and self.due_date < self.issue_date:
            raise ValidationError({
                'due_date': _('Due date cannot be before the issue date.')
            })
            
        if self.subtotal < 0:
            raise ValidationError({
                'subtotal': _('Subtotal cannot be negative.')
            })
            
        if self.tax_amount < 0:
            raise ValidationError({
                'tax_amount': _('Tax amount cannot be negative.')
            })
            
        if self.total_amount < 0:
            raise ValidationError({
                'total_amount': _('Total amount cannot be negative.')
            })
    
    def save(self, *args, **kwargs):
        """Save the invoice with proper validation and versioning."""
        # Generate invoice number if not set
        if not self.invoice_number and self.status != 'draft':
            self.invoice_number = self._generate_invoice_number()
        
        # Validate the model
        self.full_clean()
        
        # If this is an update (not a new record)
        if not self._state.adding:
            # Get the current version from the database if not provided
            if 'version' not in kwargs.get('update_fields', []) and self.pk is not None:
                try:
                    # Get the current version from the database
                    db_invoice = type(self).objects.get(pk=self.pk)
                    # If versions don't match, raise an exception
                    if str(db_invoice.version) != str(self.version):
                        raise ValueError("This invoice has been modified by another user. Please refresh and try again.")
                except type(self).DoesNotExist:
                    pass  # New record, no version check needed
            
            # Generate a new version for optimistic locking
            self.version = uuid.uuid4()
        
        # Call the parent save method
        super().save(*args, **kwargs)
    
    def _generate_invoice_number(self):
        """Generate a unique invoice number in the format INV-YYYYMMDD-XXXX
        
        Uses database-level locking to ensure uniqueness in concurrent environments.
        """
        from django.db import transaction
        
        today = timezone.now().strftime('%Y%m%d')
        base_number = f'INV-{today}'
        
        with transaction.atomic():
            # Lock the table to prevent concurrent inserts
            last_invoice = (
                Invoice.objects
                .select_for_update(nowait=True)
                .filter(invoice_number__startswith=base_number)
                .order_by('-invoice_number')
                .first()
            )
            
            if last_invoice:
                try:
                    last_num = int(last_invoice.invoice_number.split('-')[-1])
                    new_num = f"{last_num + 1:04d}"
                except (IndexError, ValueError):
                    new_num = '0001'
            else:
                new_num = '0001'
            
            return f"{base_number}-{new_num}"
            
        # Fallback to UUID if there's a locking issue
        return f"INV-{today}-{str(uuid.uuid4())[:8].upper()}"
    
    def is_payable(self):
        """Check if the invoice can be paid"""
        return self.status in ['draft', 'sent', 'pending', 'overdue']
        
    def get_tax_rate_display(self):
        """Format the tax rate for display from tax_breakdown"""
        if not self.tax_breakdown:
            return "0%"
            
        # Get the first tax rate from the breakdown (assuming a single tax rate for display)
        try:
            rate = next(iter(self.tax_breakdown.keys()))
            # Remove the multiplication by 100 since the rate is already stored as a percentage (e.g., 20.00 for 20%)
            return f"{float(rate)}%"
        except (StopIteration, ValueError, TypeError):
            return "0%"


class InvoiceItem(models.Model):
    """Represents a single line item in an invoice with tax handling.
    
    Each line item can have its own VAT rate, allowing for mixed tax rates
    within a single invoice.
    """
    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name=_('invoice')
    )
    description = models.CharField(
        max_length=200,
        verbose_name=_('description')
    )
    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=1,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name=_('quantity')
    )
    unit_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name=_('unit price')
    )
    # Fixed VAT rate at 20%
    VAT_RATE = Decimal('20.00')
    vat_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=VAT_RATE,
        editable=False,  # Make it non-editable in admin
        validators=[
            MinValueValidator(Decimal('0.00')),
            MaxValueValidator(Decimal('100.00'))
        ],
        verbose_name=_('VAT rate (%)')
    )
    total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        editable=False,
        verbose_name=_('total')
    )
    deleted = models.BooleanField(
        default=False,
        help_text=_('Designates whether this item was deleted.')
    )
    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_('Date and time when this item was deleted.')
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text=_('Date and time when this item was created.')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text=_('Date and time when this item was last updated.')
    )
    
    class Meta:
        ordering = ['id']
        verbose_name = _('Invoice Item')
        verbose_name_plural = _('Invoice Items')
    
    def __str__(self):
        return f"{self.quantity} x {self.description}"
    
    def calculate_total(self):
        """Calculate the total for this line item including tax.
        
        Returns:
            Decimal: The total amount including tax
        """
        # If either quantity or unit_price is None, set total to 0
        if self.quantity is None or self.unit_price is None:
            self.total = Decimal('0.00')
            return self.total
            
        # Calculate line total before tax
        line_total = self.quantity * self.unit_price
        
        # Calculate tax amount using the helper function
        tax_amount = quantize_money(line_total * self.vat_rate / 100)
        
        # Calculate total including tax
        self.total = quantize_money(line_total + tax_amount)
        
        return self.total
        
    def get_line_totals(self):
        """Return a dictionary with all line totals.
        
        Returns:
            dict: Contains subtotal, tax_amount, total, and vat_rate
        """
        # Calculate line total before tax
        subtotal = quantize_money(self.quantity * self.unit_price)
        
        # Calculate tax amount
        tax_amount = quantize_money(subtotal * self.vat_rate / 100)
        
        # Calculate total including tax
        total = quantize_money(subtotal + tax_amount)
        
        return {
            'subtotal': subtotal,
            'tax_amount': tax_amount,
            'total': total,
            'vat_rate': float(self.vat_rate)  # Convert to float for JSON serialization
        }
    
    def delete(self, *args, **kwargs):
        """Soft delete the item and update invoice totals."""
        from django.utils import timezone
        
        self.deleted = True
        self.deleted_at = timezone.now()
        self.save()
        
        # Update parent invoice totals
        if self.invoice_id:
            self.invoice.update_totals()
    
    def save(self, *args, **kwargs):
        """Save the item and update invoice totals."""
        # Calculate total before saving
        self.calculate_total()
        
        # Call the parent save method
        super().save(*args, **kwargs)
        
        # Update parent invoice totals if this is not a new item
        if self.invoice_id and not kwargs.get('update_fields'):
            self.invoice.update_totals()
    
    @property
    def line_total_before_tax(self):
        """Return the line total before tax."""
        return quantize_money(self.quantity * self.unit_price)
    
    @property
    def line_tax_amount(self):
        """Return the tax amount for this line."""
        return quantize_money(self.line_total_before_tax * self.vat_rate / 100)
    
    @property
    def line_total_after_tax(self):
        """Return the line total including tax."""
        return quantize_money(self.line_total_before_tax + self.line_tax_amount)


# Signal handlers
@receiver(pre_save, sender=Invoice)
def update_invoice_totals(sender, instance, **kwargs):
    """Update invoice totals before saving."""
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info(f"[signal:pre_save] Invoice pre_save signal triggered for invoice {instance.id or 'new'}")
    
    if instance.pk is None:  # New instance
        logger.info("[signal:pre_save] New invoice, skipping totals update")
        return
    
    # Only update totals if we're not already in the process of updating them
    update_fields = kwargs.get('update_fields') or []
    logger.info(f"[signal:pre_save] Update fields: {update_fields}")
    
    if not any(field in {'subtotal', 'tax_amount', 'total_amount', 'tax_breakdown'} 
              for field in update_fields):
        logger.info("[signal:pre_save] Updating invoice totals")
        instance.update_totals(save=False)
    else:
        logger.info("[signal:pre_save] Skipping totals update (already being updated)")


@receiver(post_save, sender=InvoiceItem)
def update_invoice_on_item_save(sender, instance, created, **kwargs):
    """Update the parent invoice when an item is saved."""
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info(f"[signal:post_save] InvoiceItem post_save signal triggered for item {instance.id} (created: {created})")
    
    if instance.invoice_id and not kwargs.get('raw', False):
        logger.info(f"[signal:post_save] Updating invoice {instance.invoice_id} after item save")
        try:
            instance.invoice.update_totals()
            logger.info("[signal:post_save] Invoice totals updated successfully")
        except Exception as e:
            logger.error(f"[signal:post_save] Error updating invoice totals: {str(e)}")
            raise
    else:
        logger.info("[signal:post_save] No invoice_id or raw save, skipping update")


@receiver(models.signals.post_delete, sender=InvoiceItem)
def update_invoice_on_item_delete(sender, instance, **kwargs):
    """Update the parent invoice when an item is deleted."""
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info(f"[signal:post_delete] InvoiceItem post_delete signal triggered for item {instance.id}")
    
    if instance.invoice_id and not kwargs.get('raw', False):
        logger.info(f"[signal:post_delete] Updating invoice {instance.invoice_id} after item delete")
        try:
            # Skip validation during deletion to avoid issues with required fields
            with transaction.atomic():
                # Get the invoice and update totals without validation
                from django.db.models import F
                from django.db.models.functions import Coalesce
                
                # Update the invoice directly in the database to avoid validation
                invoice = instance.invoice
                if invoice and not invoice._state.adding:
                    # Calculate new totals
                    result = invoice.update_totals(save=False)
                    
                    # Update the invoice directly in the database
                    Invoice.objects.filter(pk=invoice.pk).update(
                        subtotal=result['subtotal'],
                        tax_amount=result['tax_amount'],
                        total_amount=result['total_amount'],
                        tax_breakdown=result['tax_breakdown'],
                        version=uuid.uuid4(),
                        updated_at=timezone.now()
                    )
                    
                    logger.info("[signal:post_delete] Invoice totals updated successfully")
        except Exception as e:
            logger.error(f"[signal:post_delete] Error updating invoice totals: {str(e)}")
            # Don't raise the exception to prevent deletion from failing
    else:
        logger.info("[signal:post_delete] No invoice_id or raw delete, skipping update")
