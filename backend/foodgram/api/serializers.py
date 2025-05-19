from rest_framework import serializers
from djoser.serializers import UserCreateSerializer, UserSerializer
from django.core.files.base import ContentFile
import base64
from django.contrib.auth import get_user_model
from rest_framework.validators import UniqueTogetherValidator

from recipes.models import Ingredient, Recipe, RecipeIngredient
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


class CustomUserSerializer(UserSerializer):
    avatar = Base64ImageField(required=False)

    class Meta:
        model = FoodgramUser
        fields = ('email', 'id', 'username',
                  'first_name', 'last_name', 'avatar')


class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class IngredientInputSerializer(serializers.Serializer):
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    amount = serializers.IntegerField()


class RecipeOutputSerializer(serializers.ModelSerializer):
    ingredients = serializers.SerializerMethodField()
    author = CustomUserSerializer()

    class Meta:
        model = Recipe
        fields = ('id', 'author', 'ingredients', 'name',
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


class RecipeSerializer(serializers.ModelSerializer):
    ingredients = IngredientInputSerializer(many=True, write_only=True)
    image = Base64ImageField(required=True)

    class Meta:
        model = Recipe
        fields = ('id', 'author', 'ingredients', 'image',
                  'name', 'text', 'cooking_time')
        read_only_fields = ('author',)

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
        ingredients = validated_data.pop('ingredients')

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

class FollowSerializer(serializers.ModelSerializer):
    user = serializers.SlugRelatedField(
        slug_field='username', read_only=True,
        default=serializers.CurrentUserDefault()
    )
    following = serializers.SlugRelatedField(
        slug_field='username', queryset=User.objects.all()
    )

    class Meta:
        model = Follow
        fields = ('user', 'following',)
        read_only_fields = ('user',)

    validators = [
        UniqueTogetherValidator(
            queryset=Follow.objects.all(),
            fields=('user', 'following')
        )
    ]

    def validate_following(self, value):
        user = self.context['request'].user
        if user == value:
            raise serializers.ValidationError(
                "Нельзя подписаться на самого себя")
        return value
