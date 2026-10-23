import stripe
from decimal import Decimal
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import F
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .models import Cart, CartItem, Order, OrderItem
from catalog.models import Product
from accounts.models import Address, UserAddress

stripe.api_key = getattr(settings, 'STRIPE_SECRET_KEY', '')


#1.LOGICA DE COS (A3)

def get_or_create_user_cart(user):
    cart, _ = Cart.objects.get_or_create(user=user)
    return cart


@login_required
def view_cart(request):
    cart = get_or_create_user_cart(request.user)
    items = cart.items.select_related('product').all()
    return render(request, 'orders/cart.html', {
        'cart': cart,
        'items': items,
        'total_price': cart.total_price
    })


@require_POST
@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id, is_active=True)
    try:
        quantity = int(request.POST.get('quantity', 1))
    except (ValueError, TypeError):
        quantity = 1

    if quantity < 1:
        quantity = 1

    cart = get_or_create_user_cart(request.user)
    cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)

    new_quantity = quantity if created else cart_item.quantity + quantity

    #Validare pe server impotriva depasirii stocului disponibil (A3)
    if new_quantity > product.stock:
        return JsonResponse({
            'success': False,
            'error': f'Stoc insuficient. Doar {product.stock} unități disponibile.'
        }, status=400)

    cart_item.quantity = new_quantity
    cart_item.save()

    return JsonResponse({
        'success': True,
        'cart_count': sum(item.quantity for item in cart.items.all()),
        'total_price': float(cart.total_price)
    })


@require_POST
@login_required
def update_cart_item(request, item_id):
    cart = get_or_create_user_cart(request.user)
    cart_item = get_object_or_404(CartItem, id=item_id, cart=cart)
    
    try:
        quantity = int(request.POST.get('quantity', 1))
    except (ValueError, TypeError):
        quantity = 1

    if quantity <= 0:
        cart_item.delete()
    elif quantity > cart_item.product.stock:
        return JsonResponse({'success': False, 'error': 'Depășire stoc'}, status=400)
    else:
        cart_item.quantity = quantity
        cart_item.save()

    return JsonResponse({
        'success': True,
        'total_price': float(cart.total_price)
    })


@require_POST
@login_required
def remove_cart_item(request, item_id):
    cart = get_or_create_user_cart(request.user)
    cart_item = get_object_or_404(CartItem, id=item_id, cart=cart)
    cart_item.delete()
    return redirect('view_cart')



#2.CHECKOUT & STRIPE SESSION (A5, A6)


@login_required
def create_checkout_session(request):
    cart = get_or_create_user_cart(request.user)
    items = cart.items.select_related('product').all()

    if not items:
        return redirect('view_cart')

    #preluam sau atribuim o adresa implicita de livrare
    user_addr = UserAddress.objects.filter(user=request.user, is_default=True).first()
    if not user_addr:
        user_addr = UserAddress.objects.filter(user=request.user).first()
    
    if not user_addr:
        address = Address.objects.create(
            street_address="Strada Industriei Nr. 10",
            city="Craiova",
            postal_code="200000",
            country="Romania"
        )
        UserAddress.objects.create(user=request.user, address=address, is_default=True)
    else:
        address = user_addr.address

    #cream comanda in starea initiala "New"
    order = Order.objects.create(
        user=request.user,
        shipping_address=address,
        status='New',
        total_amount=cart.total_price
    )

    #copiem produsele din cos in order_items
    for item in items:
        OrderItem.objects.create(
            order=order,
            product=item.product,
            quantity=item.quantity,
            unit_price=item.product.price
        )

    #golim cosul utilizatorului
    items.delete()

    stripe_line_items = []
    for item in order.items.all():
        stripe_line_items.append({
            'price_data': {
                'currency': 'ron',
                'product_data': {
                    'name': item.product.name,
                },
                'unit_amount': int(item.unit_price * 100),
            },
            'quantity': item.quantity,
        })

    domain_url = request.build_absolute_uri('/')[:-1]

    checkout_session = stripe.checkout.Session.create(
        line_items=stripe_line_items,
        mode='payment',
        client_reference_id=str(order.id),
        success_url=domain_url + reverse('order_success') + f'?order_id={order.id}',
        cancel_url=domain_url + reverse('order_cancel') + f'?order_id={order.id}',
    )

    return redirect(checkout_session.url, code=303)


@login_required
def order_success(request):
    order_id = request.GET.get('order_id')
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'orders/success.html', {'order': order})


@login_required
def order_cancel(request):
    order_id = request.GET.get('order_id')
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'orders/cancel.html', {'order': order})


#3.STRIPE WEBHOOK & TRANZACTIE ATOMICA (A6, A7)

@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    webhook_secret = getattr(settings, 'STRIPE_WEBHOOK_SECRET', '')

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )
    except (ValueError, stripe.error.SignatureVerificationError):
        return HttpResponse(status=400)

    #evenimentul declansat exclusiv la confirmarea platii
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        order_id = session.get('client_reference_id')

        if order_id:
            fulfill_order_atomic(order_id, session.get('payment_intent'))

    return HttpResponse(status=200)


def fulfill_order_atomic(order_id, payment_intent_id):
    """
    Previne condițiile de concurență (Race Conditions - A7) prin
    blocarea rândurilor în tranzacție atomică SQL.[cite: 4, 26]
    """
    with transaction.atomic():
        try:
            order = Order.objects.select_for_update().get(id=order_id)
        except Order.DoesNotExist:
            return

        if order.status == 'Paid':
            return  #idempotenta impotriva trimiterilor multiple de la Stripe

        order.status = 'Paid'
        order.stripe_payment_intent = payment_intent_id
        order.save()

        #scadere atomica de stoc pentru fiecare produs
        for item in order.items.select_related('product'):
            product = Product.objects.select_for_update().get(id=item.product.id)
            if product.stock >= item.quantity:
                product.stock = F('stock') - item.quantity
                product.save()
            else:
                raise ValueError(f"Stoc epuizat pentru produsul {product.name}")