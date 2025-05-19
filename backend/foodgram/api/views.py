from django.shortcuts import render
from rest_framework import viewsets, filters
from rest_framework import viewsets, permissions
from djoser.views import UserViewSet
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import action
from django.core.files.base import ContentFile
import base64
from django.contrib.auth import get_user_model
from djoser.serializers import SetPasswordSerializer

from recipes.models import Ingredient, Recipe, Featured, ShoppingList
from users.models import Follow
from .serializers import IngredientSerializer, RecipeSerializer, CustomUserSerializer, RecipeOutputSerializer, ShortRecipeOutputSerializer, ShortUserSerializer, VeryShortUserSerializer
from .permissions import AuthorOrReadOnly

User = get_user_model()


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (filters.SearchFilter,)
    search_fields = ('^name',)
    permission_classes = (permissions.AllowAny,)


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = (AuthorOrReadOnly,)

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return RecipeSerializer
        return RecipeOutputSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(detail=True, methods=['post', 'delete'], url_path='favorite')
    def favorite(self, request, pk=None):
        user = request.user
        try:
            recipe = Recipe.objects.get(pk=pk)
        except Recipe.DoesNotExist:
            return Response({'detail': 'Страница не найдена.'}, status=status.HTTP_404_NOT_FOUND)

        if request.method == 'POST':

            if Featured.objects.filter(user=user, recipe=recipe).exists():
                return Response({'detail': 'Повторное добавление невозможно.'}, status=status.HTTP_400_BAD_REQUEST)
            featured = Featured.objects.create(user=user, recipe=recipe)
            serializer = ShortRecipeOutputSerializer(
                recipe, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        elif request.method == 'DELETE':
            featured = Featured.objects.filter(
                user=user, recipe=recipe).first()
            if not featured:
                return Response({'detail': 'Страница не найдена.'}, status=status.HTTP_400_BAD_REQUEST)
            featured.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post', 'delete'], url_path='shopping_cart')
    def shopping_cart(self, request, pk=None):
        user = request.user
        try:
            recipe = Recipe.objects.get(pk=pk)
        except Recipe.DoesNotExist:
            return Response({'detail': 'Страница не найдена.'}, status=status.HTTP_404_NOT_FOUND)

        if request.method == 'POST':

            if ShoppingList.objects.filter(user=user, recipe=recipe).exists():
                return Response({'detail': 'Повторное добавление невозможно.'}, status=status.HTTP_400_BAD_REQUEST)
            list_item = ShoppingList.objects.create(user=user, recipe=recipe)
            serializer = ShortRecipeOutputSerializer(
                recipe, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        elif request.method == 'DELETE':
            list_item = ShoppingList.objects.filter(
                user=user, recipe=recipe).first()
            if not list_item:
                return Response({'detail': 'Страница не найдена.'}, status=status.HTTP_400_BAD_REQUEST)
            list_item.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)


class CustomUserViewSet(UserViewSet):

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        user = self.get_queryset().get(id=response.data['id'])
        serializer = VeryShortUserSerializer(
            user, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'])
    def me(self, request):
        serializer = ShortUserSerializer(
            request.user, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['put', 'delete'], url_path='me/avatar')
    def avatar(self, request):
        user = request.user

        if request.method == 'PUT':
            data = request.data.get('avatar')
            try:
                format, imgstr = data.split(';base64,')
                ext = format.split('/')[-1]
                data = ContentFile(
                    base64.b64decode(imgstr), name='temp.' + ext)
            except (ValueError, AttributeError):
                return Response({'detail': 'Invalid avatar'}, status=status.HTTP_400_BAD_REQUEST)

            user.avatar.save(data.name, data)
            user.save()
            avatar_url = request.build_absolute_uri(user.avatar.url)
            return Response({'avatar': avatar_url}, status=status.HTTP_200_OK)

        elif request.method == 'DELETE':
            user.avatar.delete(save=True)
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post', 'delete'], url_path='subscribe')
    def subscribe(self, request, id=None):
        user = request.user
        try:
            following = User.objects.get(pk=id)
        except User.DoesNotExist:
            return Response({'detail': 'Страница не найдена.'}, status=status.HTTP_404_NOT_FOUND)

        if request.method == 'POST':
            if user == following:
                return Response({'detail': 'Нельзя подписаться на самого себя.'}, status=status.HTTP_400_BAD_REQUEST)

            if Follow.objects.filter(user=user, following=following).exists():
                return Response({'detail': 'Повторная подписка невозможна.'}, status=status.HTTP_400_BAD_REQUEST)
            follow = Follow.objects.create(user=user, following=following)
            serializer = CustomUserSerializer(
                following, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        elif request.method == 'DELETE':
            follow = Follow.objects.filter(
                user=user, following=following).first()
            if not follow:
                return Response({'detail': 'Страница не найдена.'}, status=status.HTTP_400_BAD_REQUEST)
            follow.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['post'])
    def set_password(self, request):
        serializer = SetPasswordSerializer(
            data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        new_password = serializer.validated_data['new_password']
        request.user.set_password(new_password)
        request.user.save()
        return Response('Пароль изменен.', status=status.HTTP_204_NO_CONTENT)

    def get_permissions(self):
        if self.action == 'retrieve':
            return [permissions.AllowAny()]
        return super().get_permissions()

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ShortUserSerializer
        return super().get_permissions()
