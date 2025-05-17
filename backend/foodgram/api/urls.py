from rest_framework.routers import DefaultRouter
from django.urls import path, include

from .views import IngredientViewSet

router = DefaultRouter()
router.register(r'ingredients', IngredientViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
