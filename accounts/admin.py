from django.contrib import admin
from .models import Address

@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ('user', 'full_name', 'street_address', 'city', 'is_default')
    list_filter = ('is_default', 'city')