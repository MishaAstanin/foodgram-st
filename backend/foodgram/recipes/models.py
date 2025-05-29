from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models


MIN_NUMBER = 1
MAX_NUMBER = 32000

User = get_user_model()


class Ingredient(models.Model):
    """Ингредиент."""

    name = models.CharField(max_length=128, verbose_name="Название")
    measurement_unit = models.CharField(max_length=64, verbose_name="Единица измерения")

    class Meta:
        verbose_name = "ингредиент"
        verbose_name_plural = "Ингредиенты"
        ordering = ["id"]

    def __str__(self):
        return f"{self.name} ({self.measurement_unit})"


class Recipe(models.Model):
    """Рецепт."""

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="Автор публикации",
        related_name="recipes",
    )
    name = models.CharField(
        max_length=256,
        verbose_name="Название",
        help_text="Название, не более 256 символов",
    )
    image = models.ImageField(upload_to="recipes_images", verbose_name="Изображение")
    text = models.TextField(verbose_name="Текстовое описание")
    ingredients = models.ManyToManyField(
        Ingredient, through="RecipeIngredient", verbose_name="Ингредиенты"
    )
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name="Время приготовления (в минутах)",
        validators=[MinValueValidator(MIN_NUMBER), MaxValueValidator(MAX_NUMBER)],
        help_text="Время приготовления (в минутах), не менее {MIN_NUMBER}",
    )
    pub_date = models.DateTimeField(
        auto_now_add=True, verbose_name="Дата и время публикации"
    )

    class Meta:
        verbose_name = "рецепт"
        verbose_name_plural = "Рецепты"
        ordering = ("-pub_date",)

    def __str__(self):
        return f"{self.name} - {self.author.get_username()}"


class RecipeIngredient(models.Model):
    """Связь рецепта и ингредиента."""

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name="Рецепт",
        related_name="recipe_ingredients",
    )
    ingredient = models.ForeignKey(
        Ingredient, on_delete=models.CASCADE, verbose_name="Ингредиент"
    )
    amount = models.PositiveSmallIntegerField(
        verbose_name="Количество",
        validators=[MinValueValidator(MIN_NUMBER), MaxValueValidator(MAX_NUMBER)],
    )

    class Meta:
        verbose_name = "связь рецепта и ингредиента"
        verbose_name_plural = "Связи рецепта и ингредиента"
        ordering = ["id"]

    def __str__(self):
        return f"{self.recipe.name} - {self.ingredient.name}: {self.amount} {self.ingredient.measurement_unit}"


class ShoppingList(models.Model):
    """Список покупок."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="Пользователь",
        related_name="shopping_list",
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name="Рецепт",
        related_name="in_shopping_list",
    )

    class Meta:
        verbose_name = "список покупок"
        verbose_name_plural = "Списки покупок"
        ordering = ["id"]

    def __str__(self):
        return f"{self.user.get_username()} - {self.recipe.name}"


class Featured(models.Model):
    """Избранное."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="Пользователь",
        related_name="featured",
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name="Рецепт",
        related_name="in_featured",
    )

    class Meta:
        verbose_name = "избранное"
        verbose_name_plural = "Избранное"
        ordering = ["id"]

    def __str__(self):
        return f"{self.user.get_username()} - {self.recipe.name}"
