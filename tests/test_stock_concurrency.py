import pytest
from decimal import Decimal
from concurrent.futures import ThreadPoolExecutor
from django.db import transaction, connection
from django.db.models import F
from catalog.models import Product
from orders.models import Order, OrderItem, Coupon


@pytest.mark.django_db(transaction=True)
class TestConcurrencyAndStockLocking:

    def test_simultaneous_checkout_zero_overselling(self, product_single_stock):
        """5. Competing checkout threads fighting for the last remaining unit (zero overselling)."""
        success_counter = []
        failure_counter = []

        def simulate_checkout(thread_id):
            connection.close()
            with transaction.atomic():
                prod = Product.objects.select_for_update().get(id=product_single_stock.id)
                if prod.stock >= 1:
                    prod.stock -= 1
                    prod.save(update_fields=["stock"])
                    success_counter.append(thread_id)
                else:
                    failure_counter.append(thread_id)

        with ThreadPoolExecutor(max_workers=2) as executor:
            executor.map(simulate_checkout, [1, 2])

        product_single_stock.refresh_from_db()
        assert len(success_counter) == 1
        assert len(failure_counter) == 1
        assert product_single_stock.stock == 0

    def test_stock_deduction_atomicity_on_order_completion(self, test_user, product_s7):
        """6. Atomic stock reduction when order transitions to Paid."""
        initial_stock = product_s7.stock
        order = Order.objects.create(
            user=test_user,
            total_amount=product_s7.price,
            status="New"
        )
        OrderItem.objects.create(order=order, product=product_s7, quantity=2, unit_price=product_s7.price)

        with transaction.atomic():
            order.status = "Paid"
            order.save(update_fields=["status"])
            for item in order.items.all():
                Product.objects.filter(id=item.product.id).update(
                    stock=item.product.stock - item.quantity
                )

        product_s7.refresh_from_db()
        assert product_s7.stock == (initial_stock - 2)

    def test_coupon_atomic_usage_cap_enforcement(self, db):
        """7. Coupon usage counter incrementation capped at max_uses."""
        coupon = Coupon.objects.create(
            code="SINGLEUSE",
            discount_type="fixed",
            discount_value=Decimal("50.00"),
            max_uses=1,
            used_count=0,
            valid_to="2030-01-01 00:00:00Z"
        )

        with transaction.atomic():
            c = Coupon.objects.select_for_update().get(id=coupon.id)
            is_valid, _ = c.is_valid()
            assert is_valid is True
            Coupon.objects.filter(id=c.id).update(used_count=F("used_count") + 1)

        coupon.refresh_from_db()
        is_valid_after, error_msg = coupon.is_valid()
        assert coupon.used_count == 1
        assert is_valid_after is False
        assert "limit" in error_msg.lower()

    def test_rollback_on_payment_failure_preserves_stock(self, product_s7):
        """8. Transaction rollback preserves stock integrity if an exception triggers."""
        initial_stock = product_s7.stock
        try:
            with transaction.atomic():
                product_s7.stock -= 1
                product_s7.save(update_fields=["stock"])
                raise RuntimeError("Payment gateway timeout simulation")
        except RuntimeError:
            pass

        product_s7.refresh_from_db()
        assert product_s7.stock == initial_stock