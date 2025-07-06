from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe

from .models import Client, ClientNote


class ClientNoteInline(admin.TabularInline):
    model = ClientNote
    extra = 0
    readonly_fields = ('created_at', 'created_by')
    fields = ('note', 'created_at', 'created_by')
    fk_name = 'client'
    
    def has_change_permission(self, request, obj=None):
        return False


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone', 'type', 'created_at', 'client_actions')
    list_filter = ('type', 'created_at')
    search_fields = ('name', 'email', 'phone', 'tax_number', 'vat_number')
    readonly_fields = ('created_at', 'updated_at', 'created_by', 'updated_by')
    fieldsets = (
        ('Basic Information', {
            'fields': ('type', 'name', 'email', 'phone', 'mobile')
        }),
        ('Tax Information', {
            'fields': ('tax_number', 'vat_number'),
            'classes': ('collapse',)
        }),
        ('Address', {
            'fields': ('address', 'city', 'state', 'postal_code', 'country')
        }),
        ('Additional Information', {
            'fields': ('website', 'notes'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        }),
    )
    inlines = [ClientNoteInline]
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('created_by', 'updated_by')
    
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)
    
    def client_actions(self, obj):
        return format_html(
            '<a class="button" href="{}">View</a>',
            reverse('admin:clients_client_change', args=[obj.id])
        )
    client_actions.short_description = 'Actions'


@admin.register(ClientNote)
class ClientNoteAdmin(admin.ModelAdmin):
    list_display = ('client', 'note_preview', 'created_by', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('client__name', 'note')
    readonly_fields = ('created_at', 'created_by')
    
    def note_preview(self, obj):
        return obj.note[:100] + '...' if len(obj.note) > 100 else obj.note
    note_preview.short_description = 'Note'
    
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
