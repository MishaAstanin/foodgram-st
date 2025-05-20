from rest_framework import serializers
from djoser.serializers import UserCreateSerializer, UserSerializer
from django.core.files.base import ContentFile
import base64
from django.contrib.auth import get_user_model
from rest_framework.validators import UniqueTogetherValidator

from recipes.models import Ingredient, Recipe, RecipeIngredient, Featured, ShoppingList
from users.models import FoodgramUser, Follow


User = get_user_model()


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)


class CustomUserCreateSerializer(UserCreateSerializer):
    class Meta:
        model = FoodgramUser
        fields = ('id', 'first_name', 'last_name',
                  'username', 'email', 'password')


class ShortRecipeOutputSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class CustomUserSerializer(UserSerializer):
    avatar = Base64ImageField(required=False)
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = FoodgramUser
        fields = ('email', 'id', 'username',
                  'first_name', 'last_name', 'is_subscribed', 'recipes', 'recipes_count', 'avatar')

    def get_recipes(self, obj):
        request = self.context.get('request')
        queryset = Recipe.objects.filter(author=obj)
        recipes_limit = request.query_params.get('recipes_limit')
        if recipes_limit is not None and recipes_limit.isdigit():
            queryset = queryset[:int(recipes_limit)]
        serializer = ShortRecipeOutputSerializer(
            queryset, many=True, context={'request': request})
        return serializer.data

    def get_is_subscribed(self, obj):
        user = self.context.get('request').user
        if user.is_authenticated:
            return Follow.objects.filter(user=user, following=obj).exists()
        return False

    def get_recipes_count(self, obj):
        return Recipe.objects.filter(author=obj).count()


class ShortUserSerializer(UserSerializer):
    avatar = Base64ImageField(required=False)
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = FoodgramUser
        fields = ('email', 'id', 'username',
                  'first_name', 'last_name', 'is_subscribed', 'avatar')

    def get_is_subscribed(self, obj):
        user = self.context.get('request').user
        if user.is_authenticated:
            return Follow.objects.filter(user=user, following=obj).exists()
        return False


class VeryShortUserSerializer(UserSerializer):

    class Meta:
        model = FoodgramUser
        fields = ('email', 'id', 'username',
                  'first_name', 'last_name')


class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class IngredientInputSerializer(serializers.Serializer):
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    amount = serializers.IntegerField(min_value=1)


class RecipeOutputSerializer(serializers.ModelSerializer):
    ingredients = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    author = ShortUserSerializer()

    class Meta:
        model = Recipe
        fields = ('id', 'author', 'ingredients', 'is_favorited', 'is_in_shopping_cart', 'name',
                  'image', 'text', 'cooking_time')
        read_only_fields = ('author',)

    def get_ingredients(self, obj):
        recipe_ingredients = RecipeIngredient.objects.filter(recipe=obj)
        return [{
            'id': ingredient.ingredient.id,
            'name': ingredient.ingredient.name,
            'measurement_unit': ingredient.ingredient.measurement_unit,
            'amount': ingredient.amount
        } for ingredient in recipe_ingredients]

    def get_is_favorited(self, obj):
        user = self.context.get('request').user
        if user.is_authenticated:
            return Featured.objects.filter(user=user, recipe=obj).exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        user = self.context.get('request').user
        if user.is_authenticated:
            return ShoppingList.objects.filter(user=user, recipe=obj).exists()
        return False


class RecipeSerializer(serializers.ModelSerializer):
    ingredients = IngredientInputSerializer(many=True, write_only=True)
    image = Base64ImageField(required=True)

    class Meta:
        model = Recipe
        fields = ('id', 'author', 'ingredients', 'image',
                  'name', 'text', 'cooking_time')
        read_only_fields = ('author',)

    def validate_ingredients(self, value):
        if not value:
            raise serializers.ValidationError("Обязательное поле.")
        ingredients_id = [ingredient.get('id') for ingredient in value]
        if len(ingredients_id) != len(set(ingredients_id)):
            raise serializers.ValidationError(
                "Ингредиенты не должны повторяться.")
        return value

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')

        recipe = Recipe.objects.create(**validated_data)

        for ingredient in ingredients:
            current_ingredient = ingredient['id']

            RecipeIngredient.objects.create(
                recipe=recipe,
                ingredient=current_ingredient,
                amount=ingredient['amount']
            )

        return recipe

    def update(self, instance, validated_data):
        ingredients = validated_data.pop('ingredients', None)
        if ingredients == None:
            raise serializers.ValidationError(
                "ingredients - обязательное поле.")

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if ingredients is not None:
            RecipeIngredient.objects.filter(recipe=instance).delete()

            for ingredient in ingredients:
                RecipeIngredient.objects.create(
                    recipe=instance,
                    ingredient=ingredient['id'],
                    amount=ingredient['amount']
                )

        return instance

    def to_representation(self, instance):
        return RecipeOutputSerializer(instance, context=self.context).data


# class FollowSerializer(serializers.ModelSerializer):
#     user = CustomUserCreateSerializer(
#         read_only=True,
#         default=serializers.CurrentUserDefault()
#     )
#     following = serializers.SlugRelatedField(
#         slug_field='username', queryset=User.objects.all()
#     )

#     class Meta:
#         model = Follow
#         fields = ('user', 'following',)
#         read_only_fields = ('user',)

#     validators = [
#         UniqueTogetherValidator(
#             queryset=Follow.objects.all(),
#             fields=('user', 'following')
#         )
#     ]

#     def validate_following(self, value):
#         user = self.context['request'].user
#         if user == value:
#             raise serializers.ValidationError(
#                 "Нельзя подписаться на самого себя.")
#         return value


# class FeaturedSerializer(serializers.ModelSerializer):
#     user = serializers.SlugRelatedField(
#         slug_field='username', read_only=True,
#         default=serializers.CurrentUserDefault()
#     )
#     recipe = serializers.PrimaryKeyRelatedField(
#         queryset=Recipe.objects.all()
#     )

#     class Meta:
#         model = Featured
#         fields = ('user', 'recipe',)
#         read_only_fields = ('user',)

#     validators = [
#         UniqueTogetherValidator(
#             queryset=Featured.objects.all(),
#             fields=('user', 'recipe')
#         )
#     ]


# class ShoppingListSerializer(serializers.ModelSerializer):
#     user = serializers.SlugRelatedField(
#         slug_field='username', read_only=True,
#         default=serializers.CurrentUserDefault()
#     )
#     recipe = serializers.PrimaryKeyRelatedField(
#         queryset=Recipe.objects.all()
#     )

#     class Meta:
#         model = ShoppingList
#         fields = ('user', 'recipe',)
#         read_only_fields = ('user',)

#     validators = [
#         UniqueTogetherValidator(
#             queryset=ShoppingList.objects.all(),
#             fields=('user', 'recipe')
#         )
#     ]
