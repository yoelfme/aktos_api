from django.urls import path

from . import views

urlpatterns = [
    path('ingest/', views.ingest_accounts, name='ingest_accounts'),
    path('', views.get_accounts, name='get_accounts'),
]
