from django.urls import path
from . import api_views

app_name = 'invoices_api'

urlpatterns = [
    path('calculate-totals/', api_views.calculate_invoice_totals, name='calculate_totals'),
]
