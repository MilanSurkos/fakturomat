from django.shortcuts import render, redirect
from django.utils import timezone
from django.db.models import Count, Sum, Q
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from invoices.models import Invoice
from clients.models import Client

class HomeView(TemplateView):
    template_name = 'core/home.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        if self.request.user.is_authenticated:
            # Get counts for dashboard cards
            context['total_invoices'] = Invoice.objects.count()
            context['paid_invoices'] = Invoice.objects.filter(status='paid').count()
            context['pending_invoices'] = Invoice.objects.filter(status='pending').count()
            context['total_clients'] = Client.objects.count()
            
            # Get recent invoices
            context['recent_invoices'] = Invoice.objects.select_related('client').order_by('-created_at')[:5]
            
            # Sample recent activities (you can replace this with a real activity log)
            context['recent_activities'] = [
                {
                    'title': 'New invoice created',
                    'description': 'Invoice #1001 was created for Test Client',
                    'timestamp': timezone.now() - timezone.timedelta(minutes=5),
                    'link': '/invoices/1/'
                },
                {
                    'title': 'Client added',
                    'description': 'New client "Test Client" was added to the system',
                    'timestamp': timezone.now() - timezone.timedelta(hours=1),
                    'link': '/clients/1/'
                },
                {
                    'title': 'Payment received',
                    'description': 'Payment of $1,000.00 received for Invoice #1000',
                    'timestamp': timezone.now() - timezone.timedelta(days=1),
                    'link': '/invoices/1/payment/'
                },
            ]
            
            # Add any other context data needed for authenticated users
            context['show_dashboard'] = True
        else:
            # Context for non-authenticated users
            context['show_dashboard'] = False
            
        return context
