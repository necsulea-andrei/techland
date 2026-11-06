from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Category, Product
from django.shortcuts import redirect
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from decimal import Decimal, InvalidOperation
from django.contrib.auth.decorators import login_required
from orders.models import Order, OrderItem
from .models import Product, Review
from .models import Product, WishlistItem
from orders.models import Cart, CartItem


def product_list(request, category_slug=None):
    category = None
    categories = Category.objects.all()
    products = Product.objects.filter(is_active=True)

    # 1. Filtrare după categorie
    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=category)

    # 2. Căutare text (nume sau SKU)
    query = request.GET.get('q', '').strip()
    if query:
        products = products.filter(
            Q(name__icontains=query) |
            Q(sku__icontains=query)
        )

    # 3. Filtrare după Price Range (min_price, max_price)
    min_price = request.GET.get('min_price', '').strip()
    max_price = request.GET.get('max_price', '').strip()

    if min_price:
        try:
            products = products.filter(price__gte=Decimal(min_price))
        except (InvalidOperation, ValueError):
            pass

    if max_price:
        try:
            products = products.filter(price__lte=Decimal(max_price))
        except (InvalidOperation, ValueError):
            pass

    # 4. Filtrare după Disponibilitate (stock)
    # stock_status: 'in_stock' (disponibil), 'out_of_stock' (indisponibil)
    stock_status = request.GET.get('stock', '').strip()
    if stock_status == 'in_stock':
        products = products.filter(stock__gt=0)
    elif stock_status == 'out_of_stock':
        products = products.filter(stock=0)

    # 5. Sortare
    sort_by = request.GET.get('sort', '-id')
    sort_mapping = {
        'price_asc': 'price',
        'price_desc': '-price',
        'date_new': '-id',
        'date_old': 'id',
    }
    order_field = sort_mapping.get(sort_by, '-id')
    products = products.order_by(order_field)

    # 6. Paginare la 12 produse
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'catalog/list.html', {
        'category': category,
        'categories': categories,
        'page_obj': page_obj,
        'query': query,
        'min_price': min_price,
        'max_price': max_price,
        'stock_status': stock_status,
        'sort_by': sort_by,
    })


def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug)
    visible_reviews = product.reviews.filter(is_visible=True).select_related('user')

    can_review = False
    user_review = None
    if request.user.is_authenticated:
        can_review = OrderItem.objects.filter(
            order__user=request.user,
            order__status='Paid',
            product=product
        ).exists()
        user_review = product.reviews.filter(user=request.user).first()

    return render(request, 'catalog/product_detail.html', {
        'product': product,
        'reviews': visible_reviews,
        'can_review': can_review,
        'user_review': user_review,
    })

def home_view(request):
    categories = Category.objects.all()
    featured_products = Product.objects.filter(is_active=True).prefetch_related('images')[:4]
    return render(request, 'catalog/home.html', {
        'categories': categories,
        'featured_products': featured_products,
    })

def contact_view(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        subject = request.POST.get('subject', '').strip()
        message = request.POST.get('message', '').strip()

        if name and email and message:
            # Opțional: trimitere email dacă Mailtrap e configurat
            # send_mail(
            #     f"[Contact TechLand] {subject}",
            #     f"Mesaj de la {name} ({email}):\n\n{message}",
            #     settings.DEFAULT_FROM_EMAIL,
            #     [settings.DEFAULT_FROM_EMAIL],
            #     fail_silently=True
            # )
            messages.success(request, "Your message has been sent successfully! We will respond as soon as possible.")
            return redirect('contact')
        else:
            messages.error(request, "Please fill in all mandatory fields.")

    return render(request, 'catalog/contact.html')


@login_required
def add_review(request, product_id):
    if request.method != 'POST':
        return redirect('product_list')

    product = get_object_or_404(Product, id=product_id)

    # 1. Verificare: a cumpărat clientul produsul într-o comandă achitată?
    has_purchased = OrderItem.objects.filter(
        order__user=request.user,
        order__status='Paid',
        product=product
    ).exists()

    if not has_purchased:
        messages.error(request, "You can leave a review only for products you have purchased!")
        return redirect('product_detail', slug=product.slug)

    # 2. Preluare date din formular
    try:
        rating = int(request.POST.get('rating', 5))
        if rating < 1 or rating > 5:
            raise ValueError
    except ValueError:
        messages.error(request, "The selected note is invalid.")
        return redirect('product_detail', slug=product.slug)

    comment = request.POST.get('comment', '').strip()

    # 3. Salvează sau actualizează recenzia existentă a utilizatorului
    review, created = Review.objects.update_or_create(
        product=product,
        user=request.user,
        defaults={
            'rating': rating,
            'comment': comment,
            'is_visible': True
        }
    )

    if created:
        messages.success(request, "Your review has been successfully published!")
    else:
        messages.success(request, "Your review has been updated!")

    return redirect('product_detail', slug=product.slug)


@login_required
def wishlist_view(request):
    """Afișează produsele salvate în wishlist-ul utilizatorului logat."""
    items = WishlistItem.objects.filter(user=request.user).select_related('product')
    return render(request, 'catalog/wishlist.html', {'wishlist_items': items})


@login_required
def toggle_wishlist(request, product_id):
    """Adaugă sau elimină produsul din wishlist (folosit din catalog sau detaliu produs)."""
    if request.method != 'POST':
        return redirect('product_list')

    product = get_object_or_404(Product, id=product_id)
    wishlist_item = WishlistItem.objects.filter(user=request.user, product=product).first()

    if wishlist_item:
        wishlist_item.delete()
        messages.info(request, f"{product.name} was removed from wishlist")
    else:
        WishlistItem.objects.create(user=request.user, product=product)
        messages.success(request, f"{product.name} was added to wishlist")

    # Întoarce utilizatorul pe pagina de unde a apăsat butonul
    return redirect(request.META.get('HTTP_REFERER', 'product_list'))


@login_required
def remove_from_wishlist(request, product_id):
    """Șterge un produs direct din pagina de Wishlist."""
    if request.method == 'POST':
        item = WishlistItem.objects.filter(user=request.user, product_id=product_id).first()
        if item:
            item.delete()
            messages.info(request, "Product was removed from wishlist.")
    return redirect('wishlist_view')


@login_required
def wishlist_to_cart(request, product_id):
    """Mută/Adaugă produsul din Wishlist direct în Coș."""
    if request.method != 'POST':
        return redirect('wishlist_view')

    product = get_object_or_404(Product, id=product_id)

    if product.stock <= 0:
        messages.error(request, f"{product.name} is currently out of stock!")
        return redirect('wishlist_view')

    # Obține sau creează coșul de cumpărături al utilizatorului
    cart, _ = Cart.objects.get_or_create(user=request.user)

    # Eliminat 'price' din defaults - se specifică doar cantitatea inițială
    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        defaults={'quantity': 1}
    )

    if not created:
        if cart_item.quantity < product.stock:
            cart_item.quantity += 1
            cart_item.save(update_fields=['quantity'])
        else:
            messages.warning(request, f"Maximum available stock reached for {product.name}.")
            return redirect('wishlist_view')

    # Elimină elementul din Wishlist după adăugarea în coș
    WishlistItem.objects.filter(user=request.user, product=product).delete()

    messages.success(request, f"{product.name} was moved to your cart!")
    return redirect('wishlist_view')