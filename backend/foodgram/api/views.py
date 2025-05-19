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

from recipes.models import Ingredient, Recipe
from users.models import Follow
from .serializers import IngredientSerializer, RecipeSerializer, CustomUserSerializer, RecipeOutputSerializer, FollowSerializer
from .permissions import AuthorOrReadOnly

User = get_user_model()


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (filters.SearchFilter,)
    search_fields = ('^name',)


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = (AuthorOrReadOnly,)

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return RecipeSerializer
        return RecipeOutputSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class CustomUserViewSet(UserViewSet):

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        user = self.get_queryset().get(id=response.data['id'])
        serializer = CustomUserSerializer(user, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'])
    def me(self, request):
        serializer = CustomUserSerializer(
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
            except (ValueError):
                return Response({'error': 'Invalid avatar'}, status=status.HTTP_400_BAD_REQUEST)

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
            return Response({'error': 'Пользователя не существует'}, status=status.HTTP_404_NOT_FOUND)

        if request.method == 'POST':
            if user == following:
                return Response({'error': 'Нельзя подписаться на самого себя'}, status=status.HTTP_400_BAD_REQUEST)

            if Follow.objects.filter(user=user, following=following).exists():
                return Response({'error': 'Повторная подписка невозможна'}, status=status.HTTP_400_BAD_REQUEST)
            follow = Follow.objects.create(user=user, following=following)
            serializer = FollowSerializer(follow, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        elif request.method == 'DELETE':
            follow = Follow.objects.filter(
                user=user, following=following).first()
            if not follow:
                return Response({'error': 'Подписки не существует'}, status=status.HTTP_400_BAD_REQUEST)
            follow.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    def get_permissions(self):
        if self.action == 'retrieve':
            return [permissions.AllowAny()]
        return super().get_permissions()
