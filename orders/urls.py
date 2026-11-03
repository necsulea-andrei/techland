from django.urls import path
from . import views

urlpatterns = [
    path('cart/', views.view_cart, name='view_cart'),
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/update/<int:item_id>/', views.update_cart_item, name='update_cart_item'),
    path('cart/remove/<int:item_id>/', views.remove_cart_item, name='remove_cart_item'),
    path('checkout/', views.create_checkout_session, name='checkout'),
    path('checkout/success/', views.order_success, name='order_success'),
    path('checkout/cancel/', views.order_cancel, name='order_cancel'),
    path('history/', views.order_history, name='order_history'),
    path('webhook/stripe/', views.stripe_webhook, name='stripe_webhook'),
    path('orders/<int:order_id>/cancel/', views.order_cancel, name='order_cancel'),
]