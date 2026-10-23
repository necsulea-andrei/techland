from django.contrib import admin
from .models import Address, UserAddress


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ('id', 'street_address', 'city', 'postal_code', 'country')
    search_fields = ('street_address', 'city', 'postal_code')
    list_filter = ('country', 'city')


@admin.register(UserAddress)
class UserAddressAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'address', 'address_type', 'is_default')
    list_filter = ('address_type', 'is_default')
    search_fields = ('user__username', 'user__email', 'address__street_address', 'address__city')