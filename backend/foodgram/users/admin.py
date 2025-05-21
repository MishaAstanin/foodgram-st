from django.contrib import admin

from .models import FoodgramUser, Follow


class FoodgramUserAdmin(admin.ModelAdmin):
    list_display = ("email", "username", "first_name", "last_name", "avatar")
    search_fields = ("email", "username")


class FollowAdmin(admin.ModelAdmin):
    list_display = ("user", "following")


admin.site.empty_value_display = "Не задано"
admin.site.register(FoodgramUser, FoodgramUserAdmin)
admin.site.register(Follow, FollowAdmin)
