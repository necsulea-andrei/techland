from django.contrib import admin
from django.utils.html import format_html
from .models import Order, OrderItem, Cart, CartItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product', 'quantity', 'unit_price', 'item_total')
    can_delete = False

    def item_total(self, obj):
        return f"{obj.unit_price * obj.quantity} RON"
    item_total.short_description = "Subtotal"


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'id', 
        'user', 
        'status_badge', 
        'total_amount', 
        'stripe_payment_intent', 
        'created_at'
    )
    list_filter = ('status', 'created_at')
    search_fields = ('id', 'user__username', 'user__email', 'stripe_payment_intent')
    readonly_fields = ('created_at', 'stripe_payment_intent', 'total_amount')
    inlines = [OrderItemInline]
    actions = ['mark_as_paid', 'mark_as_shipped', 'mark_as_delivered', 'mark_as_cancelled']
    ordering = ('-created_at',)

    def status_badge(self, obj):
        palette = {
            'New': '#f59e0b',
            'Paid': '#10b981',
            'Shipped': '#3b82f6',
            'Delivered': '#059669',
            'Cancelled': '#ef4444'
        }
        color = palette.get(obj.status, '#64748b')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 4px; font-weight: bold; font-size: 11px;">{}</span>',
            color,
            obj.status
        )
    status_badge.short_description = "Status"

    @admin.action(description="Setează status: Paid")
    def mark_as_paid(self, request, queryset):
        queryset.update(status='Paid')

    @admin.action(description="Setează status: Shipped")
    def mark_as_shipped(self, request, queryset):
        queryset.update(status='Shipped')

    @admin.action(description="Setează status: Delivered")
    def mark_as_delivered(self, request, queryset):
        queryset.update(status='Delivered')

    @admin.action(description="Setează status: Cancelled")
    def mark_as_cancelled(self, request, queryset):
        queryset.update(status='Cancelled')


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    readonly_fields = ('product', 'quantity')


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'total_items_count', 'updated_at')
    search_fields = ('user__username',)
    inlines = [CartItemInline]

    def total_items_count(self, obj):
        return obj.items.count()
    total_items_count.short_description = "Nr. Produse Unice"