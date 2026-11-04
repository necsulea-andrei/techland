from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator, ValidationError


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
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'reviews'
        unique_together = ('user', 'product')