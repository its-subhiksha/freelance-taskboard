from rest_framework.permissions import BasePermission

class IsFreelancer(BasePermission):

    def has_permission(self, request, view):
        return request.user and request.user.role == 'freelancer'

class IsClient(BasePermission):

    def has_permission(self, request, view):
        return request.user and request.user.role == 'client'