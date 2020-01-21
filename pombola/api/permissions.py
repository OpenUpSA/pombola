from __future__ import absolute_import
from rest_framework import permissions

class ReadOnly(permissions.BasePermission):
    message = 'Only read-only access is allowed'

    def has_permission(self, request, view):
        return request.method in permissions.SAFE_METHODS
