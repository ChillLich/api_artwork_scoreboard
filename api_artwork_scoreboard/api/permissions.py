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
