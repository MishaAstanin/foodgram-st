from rest_framework.routers import DefaultRouter
from django.urls import path, include

from .views import IngredientViewSet, RecipeViewSet, UserViewSet

router = DefaultRouter()
router.register(r'ingredients', IngredientViewSet)
router.register(r'users', UserViewSet)
router.register(r'recipes', RecipeViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.jwt')),
]
