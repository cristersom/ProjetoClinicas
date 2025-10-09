from django.shortcuts import redirect
from django.urls import reverse


class PatientAccessMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Regra 1: Se o usuário já está logado, pode ir para qualquer lugar.
        if request.user.is_authenticated:
            return self.get_response(request)

        # Regra 2: Lista de URLs EXATAS que um usuário anônimo PODE acessar.
        # Adicionamos as URLs de login e criar conta a esta lista.
        try:
            allowed_paths = [
                reverse('narrativa:login'),
                reverse('narrativa:criarconta'),
                reverse('narrativa:homepage'),
            ]
        except Exception:
            # Fallback para caso as URLs não estejam prontas no início
            allowed_paths = ['/login/', '/criarconta/', '/']

        # Se o caminho for um dos permitidos, deixe o usuário passar.
        if request.path in allowed_paths:
            return self.get_response(request)

        # Regra 3: Lista de ÁREAS que um usuário anônimo PODE acessar.
        # Se o caminho começar com um desses prefixos, deixe o usuário passar.
        allowed_prefixes = ['/paciente/', '/media/', '/static/', '/admin/']
        if any(request.path.startswith(prefix) for prefix in allowed_prefixes):
            return self.get_response(request)

        # Regra 4: Para TODO O RESTO, redirecione o usuário anônimo.
        return redirect('narrativa:paciente_narrativas')