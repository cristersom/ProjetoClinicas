from django.shortcuts import redirect
from django.urls import reverse


class PatientAccessMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            return self.get_response(request)

        allowed_paths = [
            reverse('narrativa:login'),
            reverse('narrativa:criarconta'),
            reverse('narrativa:homepage'),
        ]

        if (request.path in allowed_paths or
                request.path.startswith('/paciente/') or
                request.path.startswith('/media/') or
                request.path.startswith('/static/') or
                request.path.startswith('/admin/')):
            return self.get_response(request)

        return redirect('narrativa:paciente_narrativas')