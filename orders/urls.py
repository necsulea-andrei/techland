from django.urls import path
from . import views

urlpatterns = [
    #cos(A3)
    path('cart/', views.view_cart, name='view_cart'),
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/update/<int:item_id>/', views.update_cart_item, name='update_cart_item'),
    path('cart/remove/<int:item_id>/', views.remove_cart_item, name='remove_cart_item'),

    #checkout & plata stripe(A5,A6)
    path('checkout/pay/', views.create_checkout_session, name='create_checkout_session'),
    path('checkout/success/', views.order_success, name='order_success'),
    path('checkout/cancel/', views.order_cancel, name='order_cancel'),

    #webhookasincronStripe(A6,A7)
    path('api/stripe/webhook/', views.stripe_webhook, name='stripe_webhook'),
]