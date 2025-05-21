import base64

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.http import HttpResponse

from django_filters.rest_framework import DjangoFilterBackend

from djoser.serializers import SetPasswordSerializer
from djoser.views import UserViewSet

from rest_framework import filters, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.response import Response

from recipes.models import Featured, Ingredient, Recipe, RecipeIngredient, ShoppingList
from users.models import Follow

from .permissions import AuthorOrReadOnly
from .serializers import (
    BaseUserSerializer,
    ShortUserSerializer,
    CustomUserSerializer,
    IngredientSerializer,
    RecipeOutputSerializer,
    RecipeSerializer,
    ShortRecipeOutputSerializer,
)


User = get_user_model()


class IngredientSearchFilter(filters.SearchFilter):
    search_param = "name"


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (IngredientSearchFilter,)
    search_fields = ("^name",)
    permission_classes = (permissions.AllowAny,)
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = (AuthorOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ("author",)

    def handle_post_delete(self, request, pk, model, error_msg_exists):
        user = request.user
        try:
            recipe = Recipe.objects.get(pk=pk)
        except Recipe.DoesNotExist:
            return Response(
                {"detail": "Страница не найдена."}, status=status.HTTP_404_NOT_FOUND
            )

        if request.method == "POST":
            if model.objects.filter(user=user, recipe=recipe).exists():
                return Response(
                    {"detail": error_msg_exists}, status=status.HTTP_400_BAD_REQUEST
                )
            model.objects.create(user=user, recipe=recipe)
            serializer = ShortRecipeOutputSerializer(
                recipe, context={"request": request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        elif request.method == "DELETE":
            obj = model.objects.filter(user=user, recipe=recipe).first()
            if not obj:
                return Response(
                    {"detail": "Страница не найдена."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            obj.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user

        is_favorited = self.request.query_params.get("is_favorited")
        if is_favorited is not None and user.is_authenticated:
            if is_favorited == "1":
                queryset = queryset.filter(in_featured__user=user)
            elif is_favorited == "0":
                queryset = queryset.exclude(in_featured__user=user)

        is_in_shopping_cart = self.request.query_params.get("is_in_shopping_cart")
        if is_in_shopping_cart is not None and user.is_authenticated:
            if is_in_shopping_cart == "1":
                queryset = queryset.filter(in_shopping_list__user=user)
            elif is_in_shopping_cart == "0":
                queryset = queryset.exclude(in_shopping_list__user=user)
        return queryset

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return RecipeSerializer
        return RecipeOutputSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(detail=True, methods=["post", "delete"], url_path="favorite")
    def favorite(self, request, pk=None):
        return self.handle_post_delete(
            request, pk, Featured, error_msg_exists="Повторное добавление невозможно."
        )

    @action(detail=True, methods=["post", "delete"], url_path="shopping_cart")
    def shopping_cart(self, request, pk=None):
        return self.handle_post_delete(
            request,
            pk,
            ShoppingList,
            error_msg_exists="Повторное добавление невозможно.",
        )

    @action(
        detail=False,
        methods=["get"],
        url_path="download_shopping_cart",
        permission_classes=[permissions.IsAuthenticated],
    )
    def download_shopping_cart(self, request):
        user = request.user

        recipes = Recipe.objects.filter(in_shopping_list__user=user)

        ingredients = {}
        recipe_ingredients = RecipeIngredient.objects.filter(recipe__in=recipes)
        for item in recipe_ingredients:
            name = item.ingredient.name
            measurement_unit = item.ingredient.measurement_unit
            key = (name, measurement_unit)
            if key in ingredients:
                ingredients[key] += item.amount
            else:
                ingredients[key] = item.amount

        list_item = []
        for (name, measurement_unit), amount in ingredients.items():
            list_item.append(f"{name} — {amount} {measurement_unit}")
        file_content = "\n".join(list_item)

        response = HttpResponse(file_content, content_type="text/plain")
        response["Content-Disposition"] = 'attachment; filename="shopping_cart.txt"'
        return response

    @action(detail=True, methods=["get"], url_path="get-link")
    def get_link(self, request, pk=None):
        try:
            recipe = self.get_object()
        except Recipe.DoesNotExist:
            return Response(
                {"detail": "Страница не найдена."}, status=status.HTTP_404_NOT_FOUND
            )

        domain = request.get_host()
        scheme = "https" if request.is_secure() else "http"
        path = f"/recipes/{recipe.pk}"
        url = f"{scheme}://{domain}{path}"
        return Response({"short-link": url})


class CustomUserViewSet(UserViewSet):
    def get_queryset(self):
        return User.objects.all()

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        user = self.get_queryset().get(id=response.data["id"])
        serializer = BaseUserSerializer(user, context={"request": request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["get"])
    def me(self, request):
        serializer = ShortUserSerializer(request.user, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=["put", "delete"], url_path="me/avatar")
    def avatar(self, request):
        user = request.user

        if request.method == "PUT":
            data = request.data.get("avatar")
            try:
                format, imgstr = data.split(";base64,")
                ext = format.split("/")[-1]
                data = ContentFile(base64.b64decode(imgstr), name="temp." + ext)
            except (ValueError, AttributeError):
                return Response(
                    {"detail": "Invalid avatar"}, status=status.HTTP_400_BAD_REQUEST
                )

            user.avatar.save(data.name, data)
            user.save()
            avatar_url = request.build_absolute_uri(user.avatar.url)
            return Response({"avatar": avatar_url}, status=status.HTTP_200_OK)

        elif request.method == "DELETE":
            user.avatar.delete(save=True)
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["post", "delete"], url_path="subscribe")
    def subscribe(self, request, id=None):
        user = request.user
        try:
            following = User.objects.get(pk=id)
        except User.DoesNotExist:
            return Response(
                {"detail": "Страница не найдена."}, status=status.HTTP_404_NOT_FOUND
            )

        if request.method == "POST":
            if user == following:
                return Response(
                    {"detail": "Нельзя подписаться на самого себя."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if Follow.objects.filter(user=user, following=following).exists():
                return Response(
                    {"detail": "Повторная подписка невозможна."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            follow = Follow.objects.create(user=user, following=following)
            serializer = CustomUserSerializer(following, context={"request": request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        elif request.method == "DELETE":
            follow = Follow.objects.filter(user=user, following=following).first()
            if not follow:
                return Response(
                    {"detail": "Страница не найдена."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            follow.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=["get"],
        url_path="subscriptions",
        permission_classes=[permissions.IsAuthenticated],
    )
    def subscriptions(self, request):
        user = request.user
        followed_users = User.objects.filter(following__user=user)

        paginator = LimitOffsetPagination()
        paginated_users = paginator.paginate_queryset(
            followed_users, request, view=self
        )

        serializer = CustomUserSerializer(
            paginated_users, many=True, context={"request": request}
        )
        return paginator.get_paginated_response(serializer.data)

    @action(detail=False, methods=["post"])
    def set_password(self, request):
        serializer = SetPasswordSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        new_password = serializer.validated_data["new_password"]
        request.user.set_password(new_password)
        request.user.save()
        return Response("Пароль изменен.", status=status.HTTP_204_NO_CONTENT)

    def get_permissions(self):
        if self.action in ("retrieve", "list"):
            return [permissions.AllowAny()]
        return super().get_permissions()

    def get_serializer_class(self):
        if self.action in ("retrieve", "list"):
            return ShortUserSerializer
        return super().get_serializer_class()
