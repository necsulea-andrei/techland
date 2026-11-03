from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Category, Product
from django.shortcuts import redirect
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings


def product_list(request, category_slug=None):
    category = None
    categories = Category.objects.all()
    products = Product.objects.filter(is_active=True)

    query = request.GET.get('q')
    if query:
        products = products.filter(
            Q(name__icontains=query) |
            Q(sku__icontains=query)
        )

    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=category)

    # Paginare server-side la 12 produse/pagină (A1)
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'catalog/list.html', {
        'category': category,
        'categories': categories,
        'page_obj': page_obj,
        'query': query,
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