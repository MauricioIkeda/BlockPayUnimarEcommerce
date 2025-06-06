# Usuario/admin.py
from django.contrib import admin
from .models import Profile  # Remova ", ItemOrder" desta linha

admin.site.register(Profile)
# Remova a linha "admin.site.register(ItemOrder)" se ela existir
