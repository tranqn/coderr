"""Admin registration for orders."""
from django.contrib import admin

from .models import Order

admin.site.register(Order)
