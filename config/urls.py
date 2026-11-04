from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from accounts import views as account_views
from catalog import views as catalog_views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),

#Landing Page / Home dedicată
    path('', catalog_views.home_view, name='home'),

#Catalogul complet și filtrarea pe categorii (A1, B1)
    path('catalog/', catalog_views.product_list, name='product_list'),
    path('catalog/category/<slug:category_slug>/', catalog_views.product_list, name='product_list_by_category'),
    path('catalog/product/<slug:slug>/', catalog_views.product_detail, name='product_detail'),

#Auth endpoints (A4)
    path('login/', auth_views.LoginView.as_view(template_name='accounts/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('register/', account_views.register_view, name='register'),
    path('contact/', catalog_views.contact_view, name='contact'),
    path('profile/', account_views.profile_view, name='profile'),

#Orders, Cart & Stripe
    path('', include('orders.urls')),
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)