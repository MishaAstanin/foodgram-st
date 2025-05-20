from django.contrib import admin

from .models import Ingredient, Recipe, RecipeIngredient, Featured, ShoppingList


admin.site.register(
    [Ingredient, Recipe, RecipeIngredient, Featured, ShoppingList])
