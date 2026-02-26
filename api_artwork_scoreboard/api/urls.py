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
    path(
        "v1/titles/<int:title_id>/reviews/",
        views.ReviewViewset.as_view(
            {
                "get": "list",
                "post": "create",
            }
        ),
    ),
    path(
        "v1/titles/<int:title_id>/reviews/<int:pk>/",
        views.ReviewViewset.as_view(
            {
                "get": "retrieve",
                "patch": "partial_update",
                "delete": "destroy",
            }
        ),
    ),
    path(
        "v1/titles/<int:title_id>/reviews/<int:review_id>/comments/",
        views.CommentReviewViewset.as_view(
            {
                "get": "list",
                "post": "create",
            }
        ),
    ),
    path(
        "v1/titles/<int:title_id>/reviews/<int:review_id>/comments/<int:pk>/",
        views.CommentReviewViewset.as_view(
            {
                "get": "retrieve",
                "patch": "partial_update",
                "delete": "destroy",
            }
        ),
    ),
]
