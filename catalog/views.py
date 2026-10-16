from django.shortcuts import render

from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from .models import Category, Product


def product_list(request, category_slug=None):
    category = None
    categories = Category.objects.all()
    products = Product.objects.filter(is_active=True)

    # Filtrare dupa categorie (A1)
    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=category)

    # Cautare text dupa numele produsului (A2)
    query = request.GET.get('q')
    if query:
        products = products.filter(name__icontains=query.strip())

    # Paginare: 12 produse per pagina (respecta cerinta de cel mult 24 per pagina din ghid)
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'category': category,
        'categories': categories,
        'page_obj': page_obj,
        'query': query,
    }
    return render(request, 'catalog/product_list.html', context)


def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, is_active=True)
    return render(request, 'catalog/product_detail.html', {'product': product})