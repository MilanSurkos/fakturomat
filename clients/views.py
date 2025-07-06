from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, CreateView, UpdateView, DetailView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.utils import timezone
from django.db.models import Sum, Q, Count

from .models import Client, ClientNote
from invoices.models import Invoice  # Import the Invoice model
from .forms import ClientForm, ClientNoteForm


class ClientListView(LoginRequiredMixin, ListView):
    model = Client
    template_name = 'clients/client_list.html'
    context_object_name = 'clients'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filtering
        search_query = self.request.GET.get('q')
        if search_query:
            queryset = queryset.filter(
                models.Q(name__icontains=search_query) |
                models.Q(email__icontains=search_query) |
                models.Q(phone__icontains=search_query) |
                models.Q(tax_number__icontains=search_query) |
                models.Q(vat_number__icontains=search_query)
            )
            
        # Ordering
        ordering = self.request.GET.get('order_by', 'name')
        return queryset.order_by(ordering)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_clients'] = self.get_queryset().count()
        return context


class ClientCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = Client
    form_class = ClientForm
    template_name = 'clients/client_form.html'
    success_message = 'Client was created successfully.'
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('clients:detail', kwargs={'pk': self.object.pk})


class ClientDetailView(LoginRequiredMixin, DetailView):
    model = Client
    template_name = 'clients/client_detail.html'
    context_object_name = 'client'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        client = self.object
        
        # Get all invoices for this client
        invoices = Invoice.objects.filter(client=client)
        
        # Calculate statistics
        total_invoices = invoices.count()
        total_paid = invoices.filter(status='paid').aggregate(Sum('total_amount'))['total_amount__sum'] or 0
        pending_invoices = invoices.filter(status='sent').count()
        overdue_invoices = invoices.filter(due_date__lt=timezone.now().date(), status__in=['sent', 'partial']).count()
        
        # Get recent invoices (last 5)
        recent_invoices = invoices.order_by('-issue_date')[:5]
        
        # Add to context
        context.update({
            'note_form': ClientNoteForm(),
            'notes': client.client_notes.all().order_by('-created_at'),
            'total_invoices': total_invoices,
            'total_paid': total_paid,
            'pending_invoices': pending_invoices,
            'overdue_invoices': overdue_invoices,
            'recent_invoices': recent_invoices,
        })
        
        return context


class ClientUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Client
    form_class = ClientForm
    template_name = 'clients/client_form.html'
    success_message = 'Client was updated successfully.'
    
    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        form.instance.updated_at = timezone.now()
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('clients:detail', kwargs={'pk': self.object.pk})


class ClientDeleteView(LoginRequiredMixin, DeleteView):
    model = Client
    template_name = 'clients/client_confirm_delete.html'
    success_url = reverse_lazy('clients:list')
    success_message = 'Client was deleted successfully.'
    
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, self.success_message)
        return super().delete(request, *args, **kwargs)


class ClientNoteCreateView(LoginRequiredMixin, CreateView):
    model = ClientNote
    form_class = ClientNoteForm
    
    def form_valid(self, form):
        form.instance.client_id = self.kwargs['client_id']
        form.instance.created_by = self.request.user
        messages.success(self.request, 'Note added successfully.')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('clients:detail', kwargs={'pk': self.kwargs['client_id']})


def export_clients_csv(request):
    import csv
    from django.http import HttpResponse
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="clients_export.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Name', 'Email', 'Phone', 'Type', 'Tax Number', 'VAT Number', 'Address', 'City', 'Country', 'Created At'])
    
    clients = Client.objects.all().values_list(
        'name', 'email', 'phone', 'type', 'tax_number', 'vat_number', 'address', 'city', 'country', 'created_at'
    )
    
    for client in clients:
        writer.writerow(client)
    
    return response
