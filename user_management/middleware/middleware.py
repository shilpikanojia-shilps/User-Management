
from django.shortcuts import redirect
from django.conf import settings
from django.urls import resolve
from django.contrib.auth.decorators import login_required
from django.utils.deprecation import MiddlewareMixin

class NoNextLoginRedirectMiddleware(MiddlewareMixin):
    def process_view(self, request, view_func, view_args, view_kwargs):
        if not request.user.is_authenticated and getattr(view_func, 'login_required', False):
            return redirect(settings.LOGIN_URL)
        return None