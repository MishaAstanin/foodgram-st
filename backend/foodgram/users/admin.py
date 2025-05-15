from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import FoodgramUser

admin.site.register(FoodgramUser, UserAdmin)
