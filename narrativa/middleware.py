from django.shortcuts import redirect
from django.urls import reverse


class SaaSControlMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path

        # URLs que SEMPRE devem ser acessíveis (públicas)
        # Usamos strings diretas para evitar qualquer erro de reverse
        exempt_paths = [
            '/planos/',
            '/login/',
            '/criar-conta/',
            '/webhook/stripe/',
            '/pagamento/sucesso/',
            '/admin/',
        ]

        # 1. Se o caminho começar com algum dos isentos, deixa passar na hora
        if any(path.startswith(p) for p in exempt_paths) or path == '/':
            return self.get_response(request)

        # 2. Se o usuário estiver logado mas sem assinatura, manda para planos
        if request.user.is_authenticated:
            if not request.user.is_superuser:
                # Pega a clínica do usuário com segurança
                clinica = getattr(request.user, 'clinica', None)
                if not clinica or not clinica.assinatura_ativa:
                    # Se não estiver na página de planos, manda para lá
                    if path != '/planos/':
                        return redirect('/planos/')

        return self.get_response(request)