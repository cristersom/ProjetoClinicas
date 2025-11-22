from django.shortcuts import redirect
from django.urls import reverse


class PatientAccessMiddleware:
    """
    Controla o acesso de usuários não logados.
    - Se o usuário não está autenticado, ele só pode acessar rotas abertas (/login, /criarconta, /paciente/).
    - Se tentar acessar rotas que não são abertas, é forçado a ir para a área de paciente.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # 1. Se o usuário for um Admin (logado), permite o acesso a TUDO.
        if request.user.is_authenticated:
            return self.get_response(request)

        # 2. Usuário não autenticado (Paciente ou anônimo):

        # Rotas que DEVEM ser sempre acessíveis por anônimos
        try:
            allowed_paths = [
                reverse('narrativa:login'),
                reverse('narrativa:criarconta'),
                reverse('narrativa:homepage'),
                reverse('narrativa:termos_de_uso'),
                reverse('narrativa:politica_privacidade'),
                reverse('narrativa:ler_termos'),
                # A rota ler_termos_pk precisa de tratamento especial, pois tem o PK
            ]
        except Exception:
            # Fallback para caso as URLs ainda não estejam carregadas
            allowed_paths = ['/login/', '/criarconta/', '/', '/termos/', '/politica/', '/ler_termos/']

        # URLs que começam com prefixes permitidos
        allowed_prefixes = ['/paciente/', '/media/', '/static/', '/admin/']

        path_is_allowed = (
                request.path in allowed_paths or
                request.path.startswith('/ler_termos/') or  # Adiciona a exceção da rota com PK
                any(request.path.startswith(prefix) for prefix in allowed_prefixes)
        )

        if path_is_allowed:
            # Se o usuário está em uma rota permitida, deixa ele prosseguir
            return self.get_response(request)

        # 3. Se o usuário anônimo tentou acessar uma rota protegida (e.g., /narrativas/),
        # force-o para a área de paciente (que agora será barrada pelo aceite de termos).
        return redirect('narrativa:paciente_narrativas')