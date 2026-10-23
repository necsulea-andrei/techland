from django.db import models
from django.conf import settings


class Address(models.Model):
    street_address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100, default='Romania')

    class Meta:
        db_table = 'addresses'
        verbose_name_plural = 'Addresses'

    def __str__(self):
        return f"{self.street_address}, {self.city}"


class UserAddress(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='user_addresses'
    )
    address = models.ForeignKey(
        Address,
        on_delete=models.CASCADE,
        related_name='user_links'
    )
    address_type = models.CharField(max_length=20, default='shipping')
    is_default = models.BooleanField(default=False)

    class Meta:
        db_table = 'user_addresses'
        unique_together = ('user', 'address')