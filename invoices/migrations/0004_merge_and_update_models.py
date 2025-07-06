from django.db import migrations, models
import django.utils.timezone
from decimal import Decimal


def update_invoice_totals(apps, schema_editor):
    """Update all existing invoices to calculate correct totals."""
    Invoice = apps.get_model('invoices', 'Invoice')
    for invoice in Invoice.objects.all():
        # Calculate subtotal from all non-deleted items
        items = invoice.items.filter(deleted=False)
        subtotal = sum(item.total for item in items) if items.exists() else Decimal('0.00')
        
        # Calculate tax and total
        tax_rate = invoice.tax_rate if hasattr(invoice, 'tax_rate') else Decimal('20.00')
        tax_amount = (subtotal * tax_rate / 100).quantize(Decimal('0.01'))
        total_amount = (subtotal + tax_amount).quantize(Decimal('0.01'))
        
        # Update the invoice
        invoice.subtotal = subtotal
        invoice.tax_amount = tax_amount
        invoice.total_amount = total_amount
        invoice.save(update_fields=['subtotal', 'tax_amount', 'total_amount'])


class Migration(migrations.Migration):

    dependencies = [
        ('invoices', '0003_alter_invoice_options_alter_invoiceitem_options_and_more'),
    ]

    operations = [
        # Add new fields to InvoiceItem
        migrations.AddField(
            model_name='invoiceitem',
            name='deleted',
            field=models.BooleanField(default=False, help_text='Designates whether this item was deleted.'),
        ),
        migrations.AddField(
            model_name='invoiceitem',
            name='deleted_at',
            field=models.DateTimeField(blank=True, help_text='Date and time when this item was deleted.', null=True),
        ),
        migrations.AddField(
            model_name='invoiceitem',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='invoiceitem',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
        
        # Update existing fields
        migrations.AlterField(
            model_name='invoice',
            name='tax_amount',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=12, verbose_name='tax amount'),
        ),
        migrations.AlterField(
            model_name='invoice',
            name='total_amount',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=12, verbose_name='total amount'),
        ),
        migrations.AlterField(
            model_name='invoiceitem',
            name='total',
            field=models.DecimalField(decimal_places=2, editable=False, max_digits=12, verbose_name='total'),
        ),
        migrations.AlterField(
            model_name='invoiceitem',
            name='unit_price',
            field=models.DecimalField(decimal_places=2, max_digits=12, validators=[django.core.validators.MinValueValidator(Decimal('0.00'))], verbose_name='unit price'),
        ),
        migrations.AlterField(
            model_name='invoiceitem',
            name='vat_rate',
            field=models.DecimalField(decimal_places=2, default=Decimal('20.00'), max_digits=5, validators=[django.core.validators.MinValueValidator(Decimal('0.00')), django.core.validators.MaxValueValidator(Decimal('100.00'))], verbose_name='VAT rate (%)'),
        ),
        
        # Run data migration
        migrations.RunPython(update_invoice_totals, migrations.RunPython.noop),
    ]
