from decimal import Decimal
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from catalog.models import Category, Product
from accounts.models import Address, UserAddress
from orders.models import Cart, CartItem, Order, OrderItem
from orders.views import fulfill_order_atomic


class TechLandBackendTests(TestCase):
    def setUp(self):
        #1.creare User de test
        self.user = User.objects.create_user(
            username='testuser',
            email='test@techland.local',
            password='Password123!'
        )
        self.client = Client()
        self.client.login(username='testuser', password='Password123!')

        #2.creare Categorie & Produse
        self.category = Category.objects.create(
            name='Industrial PLCs',
            slug='industrial-plcs',
            description='Test PLCs'
        )
        self.product1 = Product.objects.create(
            category=self.category,
            name='Siemens S7-1200',
            slug='siemens-s7-1200',
            sku='PLC-TEST-01',
            price=Decimal('1000.00'),
            stock=10,
            is_active=True
        )
        self.product2 = Product.objects.create(
            category=self.category,
            name='Schneider M221',
            slug='schneider-m221',
            sku='PLC-TEST-02',
            price=Decimal('500.00'),
            stock=5,
            is_active=True
        )

        #3.adresa
        self.address = Address.objects.create(
            street_address='Calea Bucuresti 10',
            city='Craiova',
            postal_code='200000',
            country='Romania'
        )
        UserAddress.objects.create(user=self.user, address=self.address, is_default=True)

    #teste cos de cumparaturi & totaluri (A3)

    def test_01_create_cart_for_user(self):
        """Verifică crearea automată a unui coș persistent legat 1:1 de user."""
        cart = Cart.objects.create(user=self.user)
        self.assertEqual(cart.user, self.user)
        self.assertEqual(cart.total_price, 0)

    def test_02_add_item_to_cart(self):
        """verifica adaugarea unui produs in cos prin endpoint."""
        response = self.client.post(reverse('add_to_cart', args=[self.product1.id]), {'quantity': 2})
        self.assertEqual(response.status_code, 200)
        cart = Cart.objects.get(user=self.user)
        self.assertEqual(cart.items.count(), 1)
        self.assertEqual(cart.items.first().quantity, 2)

    def test_03_cart_server_side_total_calculation(self):
        """verifica recalcularea pe server a pretului total"""
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=cart, product=self.product1, quantity=2)  # 2 x 1000 = 2000
        CartItem.objects.create(cart=cart, product=self.product2, quantity=3)  # 3 x 500 = 1500
        self.assertEqual(cart.total_price, Decimal('3500.00'))

    def test_04_reject_quantity_above_stock(self):
        """verifica respingerea adaugarii in cos a unei cantitati peste stocul disponibil (A3)."""
        response = self.client.post(reverse('add_to_cart', args=[self.product1.id]), {'quantity': 15})
        self.assertEqual(response.status_code, 400)
        self.assertIn('Stoc insuficient', response.json().get('error', ''))

    def test_05_update_cart_item_quantity(self):
        """verifica actualizarea cantitatii unui item din cos."""
        cart = Cart.objects.create(user=self.user)
        item = CartItem.objects.create(cart=cart, product=self.product1, quantity=1)
        response = self.client.post(reverse('update_cart_item', args=[item.id]), {'quantity': 4})
        self.assertEqual(response.status_code, 200)
        item.refresh_from_db()
        self.assertEqual(item.quantity, 4)

    def test_06_remove_cart_item(self):
        """verifica stergerea unui produs din cos"""
        cart = Cart.objects.create(user=self.user)
        item = CartItem.objects.create(cart=cart, product=self.product1, quantity=1)
        response = self.client.post(reverse('remove_cart_item', args=[item.id]))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(cart.items.count(), 0)

    # --- Teste Plată, Webhook & Scădere Atomică Stoc (A6, A7) ---

    def test_07_order_creation_initial_status_new(self):
        """verifica crearea unei comenzi in starea initiala 'New'."""
        order = Order.objects.create(
            user=self.user,
            shipping_address=self.address,
            status='New',
            total_amount=Decimal('1000.00')
        )
        self.assertEqual(order.status, 'New')
        self.assertIsNone(order.stripe_payment_intent)

    def test_08_atomic_stock_decrement_on_successful_payment(self):
        """verifica scaderea atomica de stoc la confirmarea platii (A7)."""
        order = Order.objects.create(
            user=self.user,
            shipping_address=self.address,
            status='New',
            total_amount=Decimal('2000.00')
        )
        OrderItem.objects.create(
            order=order,
            product=self.product1,
            quantity=3,
            unit_price=self.product1.price
        )

        initial_stock = self.product1.stock  # 10
        fulfill_order_atomic(order.id, 'pi_test_123456')

        order.refresh_from_db()
        self.product1.refresh_from_db()

        self.assertEqual(order.status, 'Paid')
        self.assertEqual(order.stripe_payment_intent, 'pi_test_123456')
        self.assertEqual(self.product1.stock, initial_stock - 3)  # 10 - 3 = 7

    def test_09_webhook_idempotency(self):
        """verifica idempotenta: procesarea duplicat a aceluias webhook nu scade stocul de doua ori."""
        order = Order.objects.create(
            user=self.user,
            shipping_address=self.address,
            status='New',
            total_amount=Decimal('1000.00')
        )
        OrderItem.objects.create(order=order, product=self.product1, quantity=2, unit_price=self.product1.price)

        # Prima procesare
        fulfill_order_atomic(order.id, 'pi_test_unique')
        self.product1.refresh_from_db()
        self.assertEqual(self.product1.stock, 8)

        # a doua procesare cu acelasi ID (simulare retry Stripe)
        fulfill_order_atomic(order.id, 'pi_test_unique')
        self.product1.refresh_from_db()
        self.assertEqual(self.product1.stock, 8)  # ramane 8, nu scade din nou!

    def test_10_webhook_endpoint_rejects_unsigned_requests(self):
        """verifica respingerea cererilor de webhook fara semnatura valida Stripe (A6, A10)."""
        response = self.client.post(
            reverse('stripe_webhook'),
            data='{"type": "checkout.session.completed"}',
            content_type='application/json'
        )
        # Lipsa header-ului HTTP_STRIPE_SIGNATURE returneaza HTTP 400
        self.assertEqual(response.status_code, 400)

    #Teste Securitate & Permisiuni (A4, A10)

    def test_11_unauthenticated_cart_redirect(self):
        """ Verifica restrictioarea accesului la cos pentru utilizatori neautentificati."""
        self.client.logout()
        response = self.client.get(reverse('view_cart'))
        self.assertEqual(response.status_code, 302)  # Redirectionare spre login

    def test_12_password_hashing_verification(self):
        """Verifica stocarea parolei utilizatorului cu hashing securizat (nu plaintext) (A4)."""
        user = User.objects.get(username='testuser')
        self.assertNotEqual(user.password, 'Password123!')
        self.assertTrue(user.check_password('Password123!'))