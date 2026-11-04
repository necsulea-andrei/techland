from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Category, Product
from django.shortcuts import redirect
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from decimal import Decimal, InvalidOperation


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
    product = get_object_or_404(
        Product.objects.prefetch_related('images', 'reviews__user'),
        slug=slug,
        is_active=True
    )
    return render(request, 'catalog/product_detail.html', {'product': product})

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
            messages.success(request, "Mesajul tău a fost trimis cu succes! Îți vom răspunde în cel mai scurt timp.")
            return redirect('contact')
        else:
            messages.error(request, "Te rugăm să completezi toate câmpurile obligatorii.")

    return render(request, 'catalog/contact.html')