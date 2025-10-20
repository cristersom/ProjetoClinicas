from django.shortcuts import redirect
from django.urls import reverse


class PatientAccessMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            return self.get_response(request)

        try:
            allowed_paths = [
                reverse('narrativa:login'),
                reverse('narrativa:criarconta'),
                reverse('narrativa:homepage'),
            ]
        except Exception:
            allowed_paths = ['/login/', '/criarconta/', '/']

        if request.path in allowed_paths:
            return self.get_response(request)

        allowed_prefixes = ['/paciente/', '/media/', '/static/', '/admin/']
        if any(request.path.startswith(prefix) for prefix in allowed_prefixes):
            return self.get_response(request)

        return redirect('narrativa:paciente_narrativas')