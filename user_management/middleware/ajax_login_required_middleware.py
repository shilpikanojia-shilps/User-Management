# middleware/ajax_login_required_middleware.py

from django.http import JsonResponse

class AjaxLoginRequiredMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.user.is_authenticated and request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'error': 'session expired'}, status=401)
        return self.get_response(request)
