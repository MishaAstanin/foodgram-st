from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator


User = get_user_model()


class Ingredient(models.Model):
    """Ингредиент."""

    name = models.CharField(max_length=128, verbose_name='Название')
    measurement_unit = models.CharField(
        max_length=64, verbose_name='Единица измерения')

    class Meta:
        verbose_name = 'ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return f"{self.name} ({self.measurement_unit})"


class Recipe(models.Model):
    """Рецепт."""

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор публикации',
        related_name='recipes'
    )
    name = models.CharField(max_length=256, verbose_name='Название')
    image = models.ImageField(
        upload_to='recipes_images', verbose_name='Изображение')
    text = models.TextField(verbose_name='Текстовое описание')
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        verbose_name='Ингредиенты'
    )
    cooking_time = models.IntegerField(
        verbose_name='Время приготовления (в минутах)',
        validators=[MinValueValidator(1)]
    )

    class Meta:
        verbose_name = 'рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return f"{self.name} - {self.author.get_username()}"


class RecipeIngredient(models.Model):
    """Связь рецепта и ингредиента."""

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт'
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name='Ингредиент'
    )
    amount = models.IntegerField(verbose_name='Количество')

    class Meta:
        verbose_name = 'количество'
        verbose_name_plural = 'Количество'

    def __str__(self):
        return f"{self.ingredient.name}: {self.amount} {self.ingredient.measurement_unit}"
