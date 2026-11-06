from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from catalog.models import Product
from accounts.models import Address
from django.utils import timezone
from decimal import Decimal


class Cart(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='cart'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'cart'

    @property
    def total_price(self):
        return sum(item.product.price * item.quantity for item in self.items.all())


class CartItem(models.Model):
    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name='items'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE
    )
    quantity = models.IntegerField(default=1, validators=[MinValueValidator(1)])

    class Meta:
        db_table = 'cart_items'
        unique_together = ('cart', 'product')

    @property
    def subtotal(self):
        return self.product.price * self.quantity


class Order(models.Model):
    STATUS_CHOICES = [
        ('New', 'New'),
        ('Paid', 'Paid'),
        ('Shipped', 'Shipped'),
        ('Delivered', 'Delivered'),
        ('Canceled', 'Canceled'),
    ]

    SHIPPING_CHOICES = [
        ('standard', 'Standard Logistics (Free)'),
        ('express', 'Express Delivery (+49.99 RON)'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='orders')
    shipping_address = models.ForeignKey('accounts.Address', on_delete=models.SET_NULL, null=True, blank=True)
    shipping_method = models.CharField(max_length=20, choices=SHIPPING_CHOICES, default='standard')
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='New')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    stripe_payment_intent = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def str(self):
        return f"Order #{self.id} - {self.user.username} ({self.status})"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)

    @property
    def total_price(self):
        return self.unit_price * self.quantity


class Coupon(models.Model):
    DISCOUNT_TYPE_CHOICES = [
        ('percentage', 'Percentage (%)'),
        ('fixed', 'Fixed Amount (RON)'),
    ]

    code = models.CharField(max_length=50, unique=True, help_text="Ex: TECH10, PROMO50")
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPE_CHOICES, default='percentage')
    discount_value = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Percentage (e.g., 15 for 15%) or fixed value in RON"
    )
    valid_from = models.DateTimeField(default=timezone.now)
    valid_to = models.DateTimeField(help_text="Expiration date and time")
    max_uses = models.PositiveIntegerField(
        default=100, 
        help_text="Maximum total number of permitted uses"
    )
    used_count = models.PositiveIntegerField(
        default=0, 
        help_text="How many times has it already been successfully applied"
    )
    is_active = models.BooleanField(default=True)
    min_order_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=Decimal('0.00'),
        help_text="Minimum cart value required for application"
    )

    def is_valid(self, subtotal=Decimal('0.00')):
        now = timezone.now()
        if not self.is_active:
            return False, "This coupon is no longer active."
        if now < self.valid_from:
            return False, "This coupon is not yet valid."
        if now > self.valid_to:
            return False, "This coupon has expired."
        if self.used_count >= self.max_uses:
            return False, "This coupon has reached its maximum usage limit."
        if subtotal < self.min_order_amount:
            return False, f"Minimum order amount of {self.min_order_amount} RON required."
        return True, ""

    def calculate_discount(self, subtotal):
        if self.discount_type == 'percentage':
            discount = (subtotal * self.discount_value) / Decimal('100.00')
        else:
            discount = self.discount_value
        return min(discount, subtotal).quantize(Decimal('0.01'))

    def __str__(self):
        return f"{self.code} ({self.get_discount_type_display()}: {self.discount_value})"