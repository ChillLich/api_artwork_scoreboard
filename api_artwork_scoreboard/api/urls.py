from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

app_name = "api"

router = DefaultRouter()
router.register("categories", views.CategoryViewSet, basename="category")
router.register("genres", views.GenreViewSet, basename="genre")
router.register("titles", views.TitleViewSet, basename="title")

urlpatterns = [
    path("v1/auth/signup/", views.SignupView.as_view(), name="signup"),
    path("v1/auth/token/", views.TokenView.as_view(), name="token"),
    path("v1/", include(router.urls)),
]
