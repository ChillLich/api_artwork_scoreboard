from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

app_name = "api"

urlpatterns = [
    path("v1/auth/signup/", views.SignupView.as_view(), name="signup"),
    path("v1/auth/token/", views.TokenView.as_view(), name="token"),
]
