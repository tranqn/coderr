"""Admin registration for Profile."""
from django.contrib import admin

from .models import Profile

admin.site.register(Profile)
