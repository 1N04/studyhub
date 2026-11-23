"""Маршруты приложения materials."""
from django.urls import path

from . import views

app_name = 'materials'

urlpatterns = [
    path('', views.MaterialListView.as_view(), name='list'),
    path('materials/add/', views.MaterialCreateView.as_view(), name='create'),
    path('materials/<int:pk>/', views.MaterialDetailView.as_view(), name='detail'),
    path('materials/<int:pk>/edit/', views.MaterialUpdateView.as_view(), name='update'),
    path('materials/<int:pk>/delete/', views.MaterialDeleteView.as_view(), name='delete'),
    path('materials/<int:pk>/download/', views.download_material, name='download'),
    path('categories/add/', views.CategoryCreateView.as_view(), name='category_create'),
    path('categories/<int:pk>/edit/', views.CategoryUpdateView.as_view(), name='category_update'),
    path('categories/<int:pk>/delete/', views.CategoryDeleteView.as_view(), name='category_delete'),
]