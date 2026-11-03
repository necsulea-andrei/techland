from django.contrib import admin
from django.utils.html import format_html
from django.db import transaction
from .models import Order, OrderItem, Cart, CartItem
from catalog.models import Product


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product', 'quantity', 'unit_price', 'item_total')
    can_delete = False

    def item_total(self, obj):
        if obj.pk and obj.unit_price and obj.quantity:
            return f"{obj.unit_price * obj.quantity:.2f} RON"
        return "0.00 RON"
    item_total.short_description = "Subtotal"


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user',
        'status_badge',
        'status',
        'total_amount',
        'shipping_method',
        'stripe_payment_intent',
        'created_at',
    )
    list_editable = ('status',)  # Dropdown editabil direct în tabel pe câmpul real din DB
    list_filter = ('status', 'shipping_method', 'created_at')  # Filtrare pe câmpul 'status'
    search_fields = ('id', 'user__username', 'user__email', 'stripe_payment_intent')
    readonly_fields = ('created_at', 'stripe_payment_intent', 'total_amount', 'status_badge')
    inlines = [OrderItemInline]
    actions = ['mark_as_paid', 'mark_as_shipped', 'mark_as_delivered', 'mark_as_canceled']
    ordering = ('-created_at',)

    def status_badge(self, obj):
        palette = {
            'New': '#f59e0b',        # Amber
            'Paid': '#10b981',       # Emerald
            'Shipped': '#3b82f6',    # Blue
            'Delivered': '#059669',  # Green
            'Canceled': '#ef4444',   # Rose/Red
        }
        color = palette.get(obj.status, '#64748b')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 4px 10px; border-radius: 6px; font-weight: 700; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px;">{}</span>',
            color,
            obj.status
        )
    status_badge.short_description = "Status Indicator"

    def save_model(self, request, obj, form, change):
        if change and 'status' in form.changed_data:
            old_order = Order.objects.get(id=obj.id)
            # Dacă adminul schimbă statusul în Canceled dintr-o stare plătită, refacem stocul atomic
            if obj.status == 'Canceled' and old_order.status == 'Paid':
                with transaction.atomic():
                    for item in obj.items.select_related('product'):
                        prod = Product.objects.select_for_update().get(id=item.product.id)
                        prod.stock += item.quantity
                        prod.save()
        super().save_model(request, obj, form, change)

    @admin.action(description="Setează status: Paid")
    def mark_as_paid(self, request, queryset):
        queryset.update(status='Paid')

    @admin.action(description="Setează status: Shipped")
    def mark_as_shipped(self, request, queryset):
        queryset.update(status='Shipped')

    @admin.action(description="Setează status: Delivered")
    def mark_as_delivered(self, request, queryset):
        queryset.update(status='Delivered')

    @admin.action(description="Setează status: Canceled (și reface stocul)")
    def mark_as_canceled(self, request, queryset):
        with transaction.atomic():
            for order in queryset.select_related():
                if order.status == 'Paid':
                    for item in order.items.select_related('product'):
                        prod = Product.objects.select_for_update().get(id=item.product.id)
                        prod.stock += item.quantity
                        prod.save()
                order.status = 'Canceled'
                order.save()


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    readonly_fields = ('product', 'quantity')


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'total_items_count', 'created_at')
    search_fields = ('user__username',)
    readonly_fields = ('created_at',)
    inlines = [CartItemInline]

    def total_items_count(self, obj):
        return sum(item.quantity for item in obj.items.all())
    total_items_count.short_description = "Total Articole în Coș"