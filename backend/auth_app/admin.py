"""Admin registration for the custom user."""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import CustomUser

admin.site.register(CustomUser, UserAdmin)
