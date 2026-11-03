from django.contrib import admin
from django.utils.html import format_html
from .models import Category, Product, ProductImage, Review

# Personalizare Antet Admin Portal
admin.site.site_header = "TechLand Control Portal"
admin.site.site_title = "TechLand Admin"
admin.site.index_title = "Inventory & Order Management Dashboard"


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ('image_url', 'is_feature', 'image_preview')
    readonly_fields = ('image_preview',)

    def image_preview(self, obj):
        if obj.image_url:
            return format_html(
                '<img src="{}" style="width: 50px; height: 50px; object-fit: cover; border-radius: 4px;" />',
                obj.image_url
            )
        return "-"
    image_preview.short_description = "Preview"


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)
    ordering = ('id',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'sku', 'category', 'price', 'stock_badge', 'is_active')
    list_filter = ('category', 'is_active')
    search_fields = ('name', 'sku', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ('price', 'is_active')
    inlines = [ProductImageInline]
    ordering = ('-id',)

    def stock_badge(self, obj):
        if obj.stock > 5:
            color = "#10b981"  # Verde
        elif obj.stock > 0:
            color = "#f59e0b"  # Galben / Portocaliu
        else:
            color = "#ef4444"  # Roșu
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; border-radius: 9999px; font-weight: bold; font-size: 11px;">{} buc.</span>',
            color,
            obj.stock
        )
    stock_badge.short_description = "Stoc Curent"


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ('id', 'product', 'image_preview', 'image_url', 'is_feature')
    list_filter = ('is_feature',)
    search_fields = ('product__name', 'image_url')

    def image_preview(self, obj):
        if obj.image_url:
            return format_html(
                '<img src="{}" style="width: 40px; height: 40px; object-fit: cover; border-radius: 4px;" />',
                obj.image_url
            )
        return "-"
    image_preview.short_description = "Preview"


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('id', 'product', 'user', 'rating_stars', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('product__name', 'user__username', 'comment')
    readonly_fields = ('created_at',)

    def rating_stars(self, obj):
        return "★" * obj.rating + "☆" * (5 - obj.rating)
    rating_stars.short_description = "Rating"