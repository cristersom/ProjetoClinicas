from django.shortcuts import redirect
from django.urls import reverse


class PatientAccessMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Regra 1: Se o usuário já está logado, pode ir para qualquer lugar.
        if request.user.is_authenticated:
            return self.get_response(request)

        # Regra 2: Se o usuário (anônimo) está tentando acessar a área de admin, deixe-o passar.
        # É aqui que fica a página de login do admin.
        if request.path.startswith('/admin/'):
            return self.get_response(request)

        # Regra 3: Se o usuário anônimo está tentando acessar uma página de paciente, deixe-o passar.
        allowed_prefixes = ['/paciente/', '/media/', '/static/']
        if any(request.path.startswith(prefix) for prefix in allowed_prefixes):
            return self.get_response(request)

        # Regra 4: Para QUALQUER OUTRA PÁGINA (como a homepage '/', a lista de narrativas do admin, etc.),
        # redirecione o usuário anônimo para o catálogo de paciente.
        return redirect('narrativa:paciente_narrativas')