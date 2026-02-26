from rest_framework import permissions


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Разрешение позволяет:
    Безопасные методы: чтение (GET, HEAD, OPTIONS) доступно всем (даже анонимам).
    Небезопасные: создание, изменение, удаление (POST, PUT, PATCH, DELETE) только администраторам.
    Администратор- это пользователь с ролью 'admin' или суперпользователь (is_superuser).
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True

        return request.user.is_authenticated and (
            request.user.is_superuser or request.user.role == "admin"
        )


class IsModerAuthorOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.method in permissions.SAFE_METHODS or request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_authenticated and (
            obj.author == request.user
            or request.user.is_superuser
            or request.user.role in ("admin", "moderator")
        )
