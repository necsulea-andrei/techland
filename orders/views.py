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
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from .models import Cart, CartItem, Order, OrderItem, Coupon
from catalog.models import Product
from accounts.models import Address, UserAddress

stripe.api_key = getattr(settings, 'STRIPE_SECRET_KEY', '')


# =============================================================================
# 1. LOGICĂ COȘ (CART)
# =============================================================================

def get_or_create_user_cart(user):
    cart, _ = Cart.objects.get_or_create(user=user)
    return cart


def view_cart(request):
    if not request.user.is_authenticated:
        return render(request, 'orders/cart.html', {'cart': None, 'subtotal': 0, 'discount': 0, 'total': 0})

    cart, _ = Cart.objects.get_or_create(user=request.user)
    items = cart.items.select_related('product')
    
    subtotal = sum(item.product.price * item.quantity for item in items)
    discount = Decimal('0.00')
    active_coupon = None

    coupon_id = request.session.get('coupon_id')
    if coupon_id:
        coupon = Coupon.objects.filter(id=coupon_id).first()
        if coupon:
            valid, _ = coupon.is_valid(subtotal=subtotal)
            if valid:
                active_coupon = coupon
                discount = coupon.calculate_discount(subtotal)
            else:
                del request.session['coupon_id']
        else:
            del request.session['coupon_id']

    total = max(Decimal('0.00'), subtotal - discount)

    return render(request, 'orders/cart.html', {
        'cart': cart,
        'items': items,
        'subtotal': subtotal,
        'discount': discount,
        'total': total,
        'active_coupon': active_coupon,
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

    shipping_method = request.POST.get('shipping_method', 'standard')
    shipping_cost = Decimal('49.99') if shipping_method == 'express' else Decimal('0.00')

    user_addr = UserAddress.objects.filter(user=request.user, is_default=True).first()
    if not user_addr:
        user_addr = UserAddress.objects.filter(user=request.user).first()
    address = user_addr.address if user_addr else None

    # 1. Calcul subtotal produse
    subtotal = cart.total_price

    # 2. Verificare cupon din sesiune și calcul discount
    discount_amount = Decimal('0.00')
    active_coupon = None
    coupon_id = request.session.get('coupon_id')

    if coupon_id:
        coupon = Coupon.objects.filter(id=coupon_id).first()
        if coupon:
            is_valid, _ = coupon.is_valid(subtotal=subtotal)
            if is_valid:
                active_coupon = coupon
                discount_amount = coupon.calculate_discount(subtotal)
            else:
                del request.session['coupon_id']
        else:
            del request.session['coupon_id']

    # 3. Calcul total final (produse - discount + transport)
    total_with_shipping = max(Decimal('0.00'), subtotal - discount_amount) + shipping_cost

    with transaction.atomic():
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

    if shipping_cost > 0:
        stripe_line_items.append({
            'price_data': {
                'currency': 'ron',
                'product_data': {'name': 'Express Industrial Delivery'},
                'unit_amount': int(shipping_cost * 100),
            },
            'quantity': 1,
        })

    # 4. Creare cupon Stripe dinamic dacă avem discount activ
    stripe_discounts = []
    if discount_amount > 0 and active_coupon:
        stripe_coupon = stripe.Coupon.create(
            amount_off=int(discount_amount * 100),
            currency='ron',
            duration='once',
            name=f"Coupon: {active_coupon.code}"
        )
        stripe_discounts.append({'coupon': stripe_coupon.id})

    domain_url = request.build_absolute_uri('/')[:-1]
    
    checkout_session = stripe.checkout.Session.create(
        line_items=stripe_line_items,
        discounts=stripe_discounts,  # <--- Aplică reducerea direct pe Stripe Checkout
        mode='payment',
        client_reference_id=str(order.id),
        metadata={
            'order_id': order.id,
            'coupon_id': active_coupon.id if active_coupon else '',
            'discount_amount': str(discount_amount)
        },
        success_url=domain_url + reverse('order_success') + f'?order_id={order.id}&session_id={{CHECKOUT_SESSION_ID}}',
        cancel_url=domain_url + reverse('order_cancel') + f'?order_id={order.id}',
    )

    return redirect(checkout_session.url, code=303)


@login_required
def order_success(request):
    order_id = request.GET.get('order_id')
    session_id = request.GET.get('session_id')
    
    order = get_object_or_404(Order, id=order_id, user=request.user)

    # 1. Preluare email completat pe Stripe (dacă există)
    stripe_email = None
    if session_id:
        try:
            checkout_session = stripe.checkout.Session.retrieve(session_id)
            if checkout_session.customer_details:
                stripe_email = checkout_session.customer_details.email
        except Exception as e:
            print(f">>> [ERROR RETRIEVE STRIPE]: {e}")

    # 2. Marcarea comenzii ca plătită
    if order.status != 'Paid':
        order.status = 'Paid'
        order.save(update_fields=['status'])

        # Scădere stoc produse
        for item in order.items.all():
            if item.product.stock >= item.quantity:
                item.product.stock -= item.quantity
                item.product.save(update_fields=['stock'])

    # 3. GOLIREA COȘULUI UTILIZATORULUI
    user_cart = Cart.objects.filter(user=request.user).first()
    if user_cart:
        user_cart.items.all().delete()  # Șterge elementele din coș

    # Curățare cupon din sesiune
    if 'coupon_id' in request.session:
        del request.session['coupon_id']

    # 4. Trimitere email confirmare
    try:
        send_order_confirmation_email(order, recipient_email=stripe_email)
    except Exception as e:
        print(f">>> [ERROR SENT EMAIL]: {e}")

    return render(request, 'orders/success.html', {'order': order})


@require_POST
@login_required
def order_cancel(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)

    if order.status in ['Shipped', 'Delivered', 'Canceled']:
        messages.error(request, f"Order #{order.id} cannot be cancelled.")
        return redirect('profile')

    with transaction.atomic():
        # Dacă era plătită, returnăm produsele în stoc
        if order.status == 'Paid':
            for item in order.items.select_related('product'):
                prod = Product.objects.select_for_update().get(id=item.product.id)
                prod.stock += item.quantity
                prod.save()

        order.status = 'Canceled'
        order.save()

    messages.success(request, f"Order #{order.id} has been succesfully canceled and the stock has been updated.")
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
    endpoint_secret = getattr(settings, 'STRIPE_WEBHOOK_SECRET', None)

    event = None
    try:
        if endpoint_secret:
            event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
        else:
            import json
            data = json.loads(payload)
            event = stripe.Event.construct_from(data, stripe.api_key)
    except Exception as e:
        return HttpResponse(status=400)

    # Eveniment declanșat când plata a fost aprobată
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']

        # Preluare sigură ID comandă
        order_id = session.get('client_reference_id') or session.get('metadata', {}).get('order_id')

        # Preluare sigură email introdus în Stripe Checkout
        customer_details = getattr(session, 'customer_details', None) or session.get('customer_details')
        stripe_email = None
        if customer_details:
            stripe_email = getattr(customer_details, 'email', None) or customer_details.get('email')

        if order_id:
            try:
                order = Order.objects.get(id=order_id)
                if order.status != 'Paid':
                    order.status = 'Paid'
                    order.save(update_fields=['status'])

                    # Scădere stoc produse
                    for item in order.items.all():
                        if item.product.stock >= item.quantity:
                            item.product.stock -= item.quantity
                            item.product.save(update_fields=['stock'])

                    # Incrementare contor cupon (dacă s-a folosit)
                    metadata = session.get('metadata', {})
                    coupon_id = metadata.get('coupon_id') if metadata else None
                    if coupon_id:
                        Coupon.objects.filter(id=coupon_id).update(used_count=F('used_count') + 1)

                    # Golire coș utilizator după plată reușită
                    if order.user:
                        Cart.objects.filter(user=order.user).delete()

                    # Trimitere email de confirmare
                    send_order_confirmation_email(order, recipient_email=stripe_email)

            except Order.DoesNotExist:
                pass

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


@require_POST
def apply_coupon(request):
    code = request.POST.get('code', '').strip().upper()
    if not code:
        messages.error(request, "Please enter a promotional code.")
        return redirect('view_cart')

    # Calculăm subtotalul curent al coșului utilizatorului
    cart = Cart.objects.filter(user=request.user).first() if request.user.is_authenticated else None
    if not cart or not cart.items.exists():
        messages.error(request, "Your cart is empty.")
        return redirect('view_cart')

    subtotal = sum(item.product.price * item.quantity for item in cart.items.all())

    coupon = Coupon.objects.filter(code__iexact=code).first()
    if not coupon:
        messages.error(request, "Invalid coupon code.")
        return redirect('view_cart')

    is_valid, error_message = coupon.is_valid(subtotal=subtotal)
    if not is_valid:
        messages.error(request, error_message)
        return redirect('view_cart')

    # Salvăm ID-ul cuponului în sesiune
    request.session['coupon_id'] = coupon.id
    messages.success(request, f"Coupon '{coupon.code}' applied successfully!")
    return redirect('view_cart')


@require_POST
def remove_coupon(request):
    if 'coupon_id' in request.session:
        del request.session['coupon_id']
        messages.info(request, "Promotional code removed.")
    return redirect('view_cart')


def send_order_confirmation_email(order, recipient_email=None):
    subject = f"TechLand — Order Confirmation #{order.id}"
    target_email = recipient_email or (order.user.email if order.user else None)

    if not target_email:
        print(">>> [WARN MAIL] No email address for this order!")
        return

    context = {'order': order}
    html_content = render_to_string('emails/order_confirmation.html', context)
    text_content = strip_tags(html_content)

    email = EmailMultiAlternatives(
        subject=subject,
        body=text_content,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[target_email]
    )
    email.attach_alternative(html_content, "text/html")
    email.send(fail_silently=False)