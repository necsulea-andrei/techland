from .models import Cart

def cart_counter(request):
    if request.user.is_authenticated:
        cart = Cart.objects.filter(user=request.user).first()
        if cart:
            total_items = sum(item.quantity for item in cart.items.all())
            return {'navbar_cart_count': total_items}
    return {'navbar_cart_count': 0}