import base64

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile

from djoser.serializers import UserCreateSerializer, UserSerializer
from rest_framework import serializers

from recipes.models import Ingredient, Recipe, RecipeIngredient, Featured, ShoppingList


MIN_NUMBER = 1
MAX_NUMBER = 32000

User = get_user_model()


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith("data:image"):
            format, imgstr = data.split(";base64,")
            ext = format.split("/")[-1]
            data = ContentFile(base64.b64decode(imgstr), name="temp." + ext)

        return super().to_internal_value(data)


class ShortRecipeOutputSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ("id", "name", "image", "cooking_time")


class CustomUserCreateSerializer(UserCreateSerializer):
    class Meta:
        model = User
        fields = ("id", "first_name", "last_name",
                  "username", "email", "password")


class BaseUserSerializer(UserSerializer):
    class Meta:
        model = User
        fields = ("email", "id", "username", "first_name", "last_name")


class IsSubscribed(serializers.Serializer):
    is_subscribed = serializers.SerializerMethodField()

    def get_is_subscribed(self, obj):
        user = self.context["request"].user
        if user.is_authenticated:
            return user.follower.filter(following=obj).exists()
        return False


class CustomUserSerializer(UserSerializer, IsSubscribed):
    avatar = Base64ImageField(required=False)
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "email",
            "id",
            "username",
            "first_name",
            "last_name",
            "is_subscribed",
            "recipes",
            "recipes_count",
            "avatar",
        )

    def get_recipes(self, obj):
        request = self.context.get("request")
        queryset = Recipe.objects.filter(author=obj)
        recipes_limit = request.query_params.get("recipes_limit")
        if recipes_limit is not None and recipes_limit.isdigit():
            queryset = queryset[: int(recipes_limit)]
        serializer = ShortRecipeOutputSerializer(
            queryset, many=True, context={"request": request}
        )
        return serializer.data

    def get_recipes_count(self, obj):
        return Recipe.objects.filter(author=obj).count()


class ShortUserSerializer(UserSerializer, IsSubscribed):
    avatar = Base64ImageField(required=False)

    class Meta:
        model = User
        fields = (
            "email",
            "id",
            "username",
            "first_name",
            "last_name",
            "is_subscribed",
            "avatar",
        )


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ("id", "name", "measurement_unit")


class IngredientInputSerializer(serializers.Serializer):
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    amount = serializers.IntegerField(
        min_value=MIN_NUMBER,
        max_value=MAX_NUMBER,
    )


class IngredientOutputSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source="ingredient.id")
    name = serializers.ReadOnlyField(source="ingredient.name")
    measurement_unit = serializers.ReadOnlyField(
        source="ingredient.measurement_unit")

    class Meta:
        model = RecipeIngredient
        fields = ("id", "name", "measurement_unit", "amount")


class RecipeOutputSerializer(serializers.ModelSerializer):
    ingredients = IngredientOutputSerializer(
        source="recipeingredient_set", many=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    author = ShortUserSerializer()

    class Meta:
        model = Recipe
        fields = (
            "id",
            "author",
            "ingredients",
            "is_favorited",
            "is_in_shopping_cart",
            "name",
            "image",
            "text",
            "cooking_time",
        )
        read_only_fields = ("author",)

    def item_is_in_queryset(self, user, model, recipe):
        if not user.is_authenticated:
            return False
        return model.objects.filter(user=user, recipe=recipe).exists()

    def get_is_favorited(self, obj):
        user = self.context["request"].user
        return self.item_is_in_queryset(user, Featured, obj)

    def get_is_in_shopping_cart(self, obj):
        user = self.context["request"].user
        return self.item_is_in_queryset(user, ShoppingList, obj)


class RecipeSerializer(serializers.ModelSerializer):
    ingredients = IngredientInputSerializer(many=True, write_only=True)
    image = Base64ImageField(required=True)
    cooking_time = serializers.IntegerField(
        min_value=MIN_NUMBER,
        max_value=MAX_NUMBER,
    )

    class Meta:
        model = Recipe
        fields = (
            "id",
            "author",
            "ingredients",
            "image",
            "name",
            "text",
            "cooking_time",
        )
        read_only_fields = ("author",)

    def create_ingredients(self, recipe, ingredients):
        recipe_ingredients = [
            RecipeIngredient(
                recipe=recipe, ingredient=ingredient["id"], amount=ingredient["amount"]
            )
            for ingredient in ingredients
        ]
        RecipeIngredient.objects.bulk_create(recipe_ingredients)

    def validate_ingredients(self, value):
        if not value:
            raise serializers.ValidationError("Обязательное поле.")
        ingredients_id = {ingredient.get("id") for ingredient in value}
        if len(ingredients_id) != len(value):
            raise serializers.ValidationError(
                "Ингредиенты не должны повторяться.")
        return value

    def create(self, validated_data):
        ingredients = validated_data.pop("ingredients")
        recipe = Recipe.objects.create(**validated_data)
        self.create_ingredients(recipe, ingredients)
        return recipe

    def update(self, instance, validated_data):
        ingredients = validated_data.pop("ingredients", None)
        if ingredients is None:
            raise serializers.ValidationError(
                "ingredients - обязательное поле.")

        instance.recipe_ingredients.all().delete()

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        self.create_ingredients(instance, ingredients)
        return instance

    def to_representation(self, instance):
        return RecipeOutputSerializer(instance, context=self.context).data
