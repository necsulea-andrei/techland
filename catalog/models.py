from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator, ValidationError
from django.db.models import Avg


class Category(models.Model):
    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=140, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        db_table = 'categories'
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.name


class Product(models.Model):
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name='products'
    )
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True)
    sku = models.CharField(max_length=64, unique=True)
    price = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        validators=[MinValueValidator(0.01)]
    )
    stock = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    description = models.TextField(blank=True, default='')
    is_active = models.BooleanField(default=True)

    @property
    def average_rating(self):
        """Returnează media review-urilor vizibile (rotunjită la 1 zecimală) sau 0."""
        avg = self.reviews.filter(is_visible=True).aggregate(Avg('rating'))['rating__avg']
        return round(avg, 1) if avg else 0

    @property
    def reviews_count(self):
        """Numărul total de recenzii vizibile."""
        return self.reviews.filter(is_visible=True).count()

    class Meta:
        db_table = 'products'

    def __str__(self):
        return f"{self.name} (SKU: {self.sku})"


class ProductImage(models.Model):
    SOURCE_CHOICES = [
        ('upload', 'Uploaded file'),
        ('url', 'URL - external link'),
    ]

    product = models.ForeignKey(
        'Product', 
        on_delete=models.CASCADE, 
        related_name='images'
    )

    # Câmpul de selectare a sursei active
    source_type = models.CharField(
        max_length=10,
        choices=SOURCE_CHOICES,
        default='url',
        verbose_name="Active image source"
    )

    # 1. Pentru fișiere încărcate de pe disc din Admin Panel
    image = models.ImageField(
        upload_to='products/%Y/%m/', 
        blank=True, 
        null=True,
        help_text="Upload an image..."
    )
    # 2. Pentru link-uri externe vechi sau CDN
    image_url = models.URLField(
        max_length=1000, 
        blank=True, 
        null=True,
        help_text="URL (https://...)"
    )
    alt_text = models.CharField(max_length=255, blank=True)

    def clean(self):
        super().clean()
        if self.source_type == 'upload' and not self.image:
            raise ValidationError({
                'image': 'Ai selectat "Uploaded file" ca sursă activă, dar nu ai încărcat niciun fișier.'
            })
        if self.source_type == 'url' and not self.image_url:
            raise ValidationError({
                'image_url': 'Ai selectat "URL" ca sursă activă, dar câmpul Image URL este gol.'
            })

    @property
    def display_url(self):
        if self.source_type == 'upload' and self.image:
            try:
                return self.image.url   # <--- .url adaugă automat '/media/' în față!
            except ValueError:
                return ""
        elif self.source_type == 'url' and self.image_url:
            return self.image_url
        return ""


class Review(models.Model):
    product = models.ForeignKey(
        'Product', 
        on_delete=models.CASCADE, 
        related_name='reviews'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='reviews'
    )
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Rating between 1 and 5"
    )
    comment = models.TextField(blank=True)
    is_visible = models.BooleanField(
        default=True, 
        verbose_name="Publicly visible",
        help_text="Uncheck to hide the review from the store without deleting it."
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        # Un utilizator poate lăsa un singur review per produs
        unique_together = ('product', 'user')

    def __str__(self):
        return f"{self.user.username} - {self.product.name} ({self.rating}★)"


class WishlistItem(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='wishlist_items'
    )
    product = models.ForeignKey(
        'Product',
        on_delete=models.CASCADE,
        related_name='wishlisted_by'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ('user', 'product')  # Previne dublarea aceluiași produs în wishlist

    def __str__(self):
        return f"{self.user.username} - {self.product.name}"