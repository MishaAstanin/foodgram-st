from django.contrib import admin

from .models import Ingredient, Recipe, RecipeIngredient, Featured, ShoppingList

admin.site.register(Ingredient)
admin.site.register(Recipe)
admin.site.register(RecipeIngredient)
admin.site.register(Featured)
admin.site.register(ShoppingList)