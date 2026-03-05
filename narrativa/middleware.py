from django.shortcuts import redirect
from django.urls import reverse

class SaaSControlMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # 1. Lista de URLs que SEMPRE devem ser acessíveis (públicas)
        path = request.path
        exempt_urls = [
            reverse('narrativa:home'),
            reverse('narrativa:login'),
            reverse('narrativa:criarconta'),
            reverse('narrativa:planos'),  # ADICIONADO: Planos agora é livre
            reverse('narrativa:stripe_webhook'),
            '/admin/',
        ]

        # 2. Se a URL atual estiver na lista acima, deixa passar direto
        if any(path.startswith(url) for url in exempt_urls):
            return self.get_response(request)

        # 3. Se o usuário estiver logado, mas sem assinatura ativa, manda para planos
        if request.user.is_authenticated:
            if not request.user.is_superuser:
                clinica = getattr(request.user, 'clinica', None)
                if not clinica or not clinica.assinatura_ativa:
                    if path != reverse('narrativa:planos'):
                        return redirect('narrativa:planos')

        return self.get_response(request)