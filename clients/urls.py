from django.urls import path
from . import views

app_name = 'clients'

urlpatterns = [
    # Client URLs
    path('', views.ClientListView.as_view(), name='list'),
    path('create/', views.ClientCreateView.as_view(), name='create'),
    path('<int:pk>/', views.ClientDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/', views.ClientUpdateView.as_view(), name='edit'),
    path('<int:pk>/delete/', views.ClientDeleteView.as_view(), name='delete'),
    
    # Client Note URLs
    path('<int:client_id>/notes/add/', views.ClientNoteCreateView.as_view(), name='add_note'),
    
    # Export URLs
    path('export/csv/', views.export_clients_csv, name='export_csv'),
]
