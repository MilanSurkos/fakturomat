from django.contrib import admin
from django.utils.html import format_html
from .models import Invoice, InvoiceItem


class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 1
    fields = ('description', 'quantity', 'unit_price', 'vat_rate', 'total')
    readonly_fields = ('total',)
    
    def total(self, instance):
        return f"{instance.total:.2f}"
    total.short_description = 'Total'


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'client', 'issue_date', 'due_date', 'status', 'display_total', 'payment_method', 'currency')
    list_filter = ('status', 'issue_date', 'due_date', 'payment_method', 'currency')
    search_fields = ('invoice_number', 'client__name', 'client__email')
    date_hierarchy = 'issue_date'
    inlines = [InvoiceItemInline]
    readonly_fields = ('subtotal', 'tax_amount', 'total_amount', 'created_at', 'updated_at', 'created_by')
    fieldsets = (
        ('Invoice Information', {
            'fields': ('invoice_number', 'client', 'issue_date', 'due_date', 'status', 'payment_method', 'currency')
        }),
        ('Financial Details', {
            'fields': ('subtotal', 'tax_amount', 'total_amount')
        }),
        ('Additional Information', {
            'fields': ('notes', 'created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def display_total(self, obj):
        return f"{obj.total_amount:.2f} {obj.currency}"
    display_total.short_description = 'Total'
    
    def save_model(self, request, obj, form, change):
        if not obj.pk:  # Only set created_by during the first save.
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(InvoiceItem)
class InvoiceItemAdmin(admin.ModelAdmin):
    list_display = ('invoice', 'description', 'quantity', 'unit_price', 'vat_rate', 'display_total')
    list_filter = ('invoice__status', 'vat_rate')
    search_fields = ('description', 'invoice__invoice_number')
    readonly_fields = ('total',)
    
    def display_total(self, obj):
        return f"{obj.total:.2f} {obj.invoice.currency}"
    display_total.short_description = 'Total'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('invoice')
