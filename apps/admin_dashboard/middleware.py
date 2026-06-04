from django.shortcuts import redirect
from django.contrib import messages


class PreviewModeMiddleware:
    """
    Handles admin 'Connect as User' sandbox mode.

    When active (session has 'preview_mode' = True):
    - Sets request.preview_mode = True on every request
    - Blocks all non-safe HTTP methods (POST/PUT/PATCH/DELETE) except the
      disconnect endpoint, so nothing gets written to the database
    """

    SAFE_METHODS = frozenset(['GET', 'HEAD', 'OPTIONS', 'TRACE'])

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        is_preview = bool(request.session.get('preview_mode', False))
        request.preview_mode = is_preview

        if is_preview and request.method not in self.SAFE_METHODS:
            # Always allow the disconnect endpoint so admin can exit
            if request.path.rstrip('/') == '/dashboard/disconnect':
                return self.get_response(request)

            # AJAX / fetch callers get a JSON 403
            accept = request.headers.get('Accept', '')
            xhr = request.headers.get('X-Requested-With', '')
            if xhr == 'XMLHttpRequest' or 'application/json' in accept:
                from django.http import JsonResponse
                return JsonResponse(
                    {'error': 'Preview mode: changes are not saved.'},
                    status=403,
                )

            # Regular form submissions – bounce back with a warning
            messages.warning(
                request,
                'Preview mode active — this action was blocked. Changes are not saved.',
            )
            referer = request.META.get('HTTP_REFERER', '/')
            return redirect(referer)

        return self.get_response(request)
