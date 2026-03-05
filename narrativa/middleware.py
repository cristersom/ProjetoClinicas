from django.shortcuts import redirect
from django.urls import reverse, NoReverseMatch


class SaaSControlMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Lista de caminhos que não precisam de verificação
        try:
            exempt_urls = [
                reverse('narrativa:home'),
                reverse('narrativa:planos'),
                reverse('narrativa:login'),
                reverse('admin:index'),
            ]
            # Tenta adicionar criarconta se existir
            try:
                exempt_urls.append(reverse('narrativa:criarconta'))
            except NoReverseMatch:
                pass

        except NoReverseMatch:
            exempt_urls = []

        # Se o usuário não está logado e tenta acessar algo fora da lista, manda pra home
        if not request.user.is_authenticated and request.path not in exempt_urls:
            return redirect('narrativa:home')

        response = self.get_response(request)
        return response