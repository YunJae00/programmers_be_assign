from rest_framework.permissions import BasePermission


class HasRolePermission(BasePermission):
    def __init__(self, allowed_roles, message=None):
        self.allowed_roles = allowed_roles
        self.message = message or "엑세스 권한이 없습니다."

    def has_permission(self, request, view):
        return request.user.role in self.allowed_roles
