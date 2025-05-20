from django.contrib import admin

from .models import Ingredient, Recipe, RecipeIngredient, Featured, ShoppingList


class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        'author',
        'name',
        'image',
        'text',
        'get_ingredients',
        'cooking_time',
        'pub_date',
        'featured_count',
    )
    search_fields = ('author__username', 'name')

    @admin.display(description='Ингредиенты')
    def get_ingredients(self, obj):
        return ", ".join([ingredient.name for ingredient in obj.ingredients.all()])

    @admin.display(description='Количество в избранном')
    def featured_count(self, obj):
        return obj.in_featured.count()


class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    search_fields = ('name',)


admin.site.empty_value_display = 'Не задано'
admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(Recipe, RecipeAdmin)


admin.site.register(
    [RecipeIngredient, Featured, ShoppingList])
