import pytest
from decimal import Decimal
from django.contrib.auth import get_user_model
from catalog.models import Category, Product

User = get_user_model()


@pytest.fixture
def test_user(db):
    return User.objects.create_user(
        username="unit_tester",
        email="tester@techland.local",
        password="SafePassword123!"
    )


@pytest.fixture
def sample_category(db):
    return Category.objects.create(name="PLCs & Automation", slug="plcs-automation")


@pytest.fixture
def product_s7(db, sample_category):
    return Product.objects.create(
        category=sample_category,
        name="Siemens SIMATIC S7-1200",
        slug="siemens-s7-1200",
        sku="PLC-SIEM-S712",
        price=Decimal("1200.00"),
        stock=10
    )


@pytest.fixture
def product_single_stock(db, sample_category):
    return Product.objects.create(
        category=sample_category,
        name="Schneider Modicon M221",
        slug="schneider-m221",
        sku="PLC-SCHN-M221",
        price=Decimal("850.50"),
        stock=1
    )