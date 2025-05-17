from django.shortcuts import render
from rest_framework import viewsets, filters


from recipes.models import Ingredient, Recipe
from users.models import FoodgramUser
from .serializers import IngredientSerializer, RecipeSerializer, CustomUserSerializer, RecipeOutputSerializer


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (filters.SearchFilter,)
    search_fields = ('^name',)


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return RecipeSerializer
        return RecipeOutputSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

class UserViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = FoodgramUser.objects.all()
    serializer_class = CustomUserSerializer