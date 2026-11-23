"""Маршруты REST API."""
from django.urls import path

from . import views

app_name = 'api'

urlpatterns = [
    path('categories/', views.CategoryListView.as_view(), name='category-list'),
    path('materials/', views.MaterialListCreateView.as_view(), name='material-list'),
    path('materials/<int:pk>/', views.MaterialDetailView.as_view(), name='material-detail'),
    path(
        'materials/<int:pk>/downloads/',
        views.MaterialDownloadLogView.as_view(),
        name='material-downloads',
    ),
]