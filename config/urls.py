"""
URL configuration for config project.
"""
from django.contrib import admin
from django.urls import path, include  # <-- 1. Am adăugat include
from django.contrib.auth import views as auth_views
from accounts import views as account_views
from catalog import views as catalog_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', catalog_views.product_list, name='product_list'),
    path('category/<slug:category_slug>/', catalog_views.product_list, name='product_list_by_category'),
    path('product/<slug:slug>/', catalog_views.product_detail, name='product_detail'),

    # Auth endpoints (A4)
    path('login/', auth_views.LoginView.as_view(template_name='accounts/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('register/', account_views.register_view, name='register'),

    #Orders, Cart & Stripe Checkout (A3, A5, A6)
    path('', include('orders.urls')),
]