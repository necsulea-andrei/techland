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
from django.contrib import messages

from .models import Cart, CartItem, Order, OrderItem
from catalog.models import Product
from accounts.models import Address, UserAddress

stripe.api_key = getattr(settings, 'STRIPE_SECRET_KEY', '')


# =============================================================================
# 1. LOGICĂ COȘ (CART)
# =============================================================================

def get_or_create_user_cart(user):
    cart, _ = Cart.objects.get_or_create(user=user)
    return cart


@login_required
def view_cart(request):
    cart = get_or_create_user_cart(request.user)
    items = cart.items.select_related('product', 'product__category').all()
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

    # Verificare limită stoc curent
    if new_quantity > product.stock:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'error': f'Stoc insuficient. Doar {product.stock} bucăți disponibile.'
            }, status=400)
        return redirect('product_detail', slug=product.slug)

    cart_item.quantity = new_quantity
    cart_item.save()

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'cart_count': sum(item.quantity for item in cart.items.all()),
            'total_price': float(cart.total_price)
        })

    return redirect('view_cart')


@require_POST
@login_required
def update_cart_item(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    
    try:
        new_qty = int(request.POST.get('quantity', 1))
    except (ValueError, TypeError):
        return JsonResponse({'success': False, 'error': 'Cantitate invalidă'}, status=400)

    if new_qty < 1:
        return JsonResponse({'success': False, 'error': 'Cantitatea minimă este 1'}, status=400)
    
    if new_qty > cart_item.product.stock:
        return JsonResponse({
            'success': False, 
            'error': f'Stoc maxim disponibil: {cart_item.product.stock}'
        }, status=400)

    cart_item.quantity = new_qty
    cart_item.save()

    item_total = cart_item.product.price * cart_item.quantity
    cart_total = cart_item.cart.total_price

    return JsonResponse({
        'success': True,
        'quantity': cart_item.quantity,
        'item_total': f"{item_total:.2f}",
        'cart_total': f"{cart_total:.2f}"
    })


@require_POST
@login_required
def remove_cart_item(request, item_id):
    cart = get_or_create_user_cart(request.user)
    cart_item = get_object_or_404(CartItem, id=item_id, cart=cart)
    cart_item.delete()
    return redirect('view_cart')


# =============================================================================
# 2. CHECKOUT & STRIPE SESSION
# =============================================================================

@login_required
def create_checkout_session(request):
    cart = get_or_create_user_cart(request.user)
    items = cart.items.select_related('product').all()

    if not items.exists():
        return redirect('view_cart')

    # Alegere metodă livrare (standard / express)
    shipping_method = request.POST.get('shipping_method', 'standard')
    shipping_cost = Decimal('49.99') if shipping_method == 'express' else Decimal('0.00')

    user_addr = UserAddress.objects.filter(user=request.user, is_default=True).first()
    if not user_addr:
        user_addr = UserAddress.objects.filter(user=request.user).first()
    
    address = user_addr.address if user_addr else None

    # Creare comandă cu cost livrare
    total_with_shipping = cart.total_price + shipping_cost
    order = Order.objects.create(
        user=request.user,
        shipping_address=address,
        shipping_method=shipping_method,
        shipping_cost=shipping_cost,
        status='New',
        total_amount=total_with_shipping
    )

    stripe_line_items = []
    for item in items:
        OrderItem.objects.create(
            order=order,
            product=item.product,
            quantity=item.quantity,
            unit_price=item.product.price
        )
        stripe_line_items.append({
            'price_data': {
                'currency': 'ron',
                'product_data': {'name': item.product.name},
                'unit_amount': int(item.product.price * 100),
            },
            'quantity': item.quantity,
        })

    # Adăugare linie Stripe pentru transport dacă este express
    if shipping_cost > 0:
        stripe_line_items.append({
            'price_data': {
                'currency': 'ron',
                'product_data': {'name': 'Express Industrial Delivery'},
                'unit_amount': int(shipping_cost * 100),
            },
            'quantity': 1,
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
    
    # Curățăm coșul doar după ce sesiunea s-a încheiat cu succes
    cart = get_or_create_user_cart(request.user)
    cart.items.all().delete()
    
    return render(request, 'orders/success.html', {'order': order})


@require_POST
@login_required
def order_cancel(request, order_id):
    """Permite utilizatorului să anuleze comanda doar dacă nu a fost expediată și returnează stocul."""
    order = get_object_or_404(Order, id=order_id, user=request.user)

    if order.status not in ['New', 'Paid']:
        messages.error(request, "Această comandă a fost deja expediată sau procesată și nu mai poate fi anulată direct.")
        return redirect('profile')

    with transaction.atomic():
        # Dacă era plătită (adică stocul fusese deja scăzut), restaurăm stocul atomic
        if order.status == 'Paid':
            for item in order.items.select_related('product'):
                prod = Product.objects.select_for_update().get(id=item.product.id)
                prod.stock += item.quantity
                prod.save()

        order.status = 'Canceled'
        order.save()

    messages.success(request, f"Comanda #{order.id} a fost anulată cu succes, iar stocul a fost actualizat.")
    return redirect('profile')

@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user).prefetch_related('items__product').order_by('-created_at')
    return render(request, 'orders/history.html', {'orders': orders})


# =============================================================================
# 3. STRIPE WEBHOOK & TRANZACȚIE ATOMICĂ
# =============================================================================

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

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        order_id = session.get('client_reference_id')

        if order_id:
            try:
                fulfill_order_atomic(order_id, session.get('payment_intent'))
            except ValueError as err:
                return HttpResponse(str(err), status=409)

    return HttpResponse(status=200)


def fulfill_order_atomic(order_id, payment_intent_id):
    """
    Previne condițiile de concurență (Race Conditions) prin
    blocarea rândurilor în tranzacție atomică SQL via select_for_update.[cite: 4]
    """
    with transaction.atomic():
        try:
            order = Order.objects.select_for_update().get(id=order_id)
        except Order.DoesNotExist:
            return

        if order.status == 'Paid':
            return  # Idempotență împotriva trimiterilor duplicate de la Stripe

        # Verificare și scădere atomică pentru fiecare produs
        for item in order.items.select_related('product'):
            product = Product.objects.select_for_update().get(id=item.product.id)
            if product.stock >= item.quantity:
                product.stock = product.stock - item.quantity
                product.save()
            else:
                raise ValueError(f"Stoc epuizat pentru produsul {product.name}")

        order.status = 'Paid'
        order.stripe_payment_intent = payment_intent_id
        order.save()