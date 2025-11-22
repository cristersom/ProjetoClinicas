from django.shortcuts import redirect
from django.urls import reverse
from django.conf import settings  # Importa settings para usar a chave de sessão


class PatientAccessMiddleware:
    """
    Controla o acesso de usuários não logados e impõe a tela de aceite de termos
    para todas as rotas do fluxo do paciente.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # 1. Se o usuário for um Admin (logado), permite o acesso a TUDO.
        if request.user.is_authenticated:
            return self.get_response(request)

        path = request.path
        # Pega a chave de settings para consistência
        TERMOS_ACEITOS_KEY = getattr(settings, 'TERMOS_ACEITOS_KEY', 'termo_aceite_session')

        # Rotas permitidas para anônimos, que não devem ser redirecionadas para o aceite
        try:
            allowed_paths = [
                reverse('narrativa:login'),
                reverse('narrativa:criarconta'),
                reverse('narrativa:homepage'),
                reverse('narrativa:termos_de_uso'),
                reverse('narrativa:politica_privacidade'),
                reverse('narrativa:ler_termos'),  # A rota de aceite base
            ]
            # URLs base para as quais precisamos extrair o ID
            cena_base_url = reverse('narrativa:exibir_cena_paciente', args=[0])[:-2]
            questionario_base_url = reverse('narrativa:responder_questionario', args=[0])[:-2]
        except Exception:
            # Fallback para evitar erro na inicialização
            allowed_paths = ['/login/', '/criarconta/', '/', '/termos/', '/politica/', '/ler_termos/']
            cena_base_url = '/paciente/cena/'
            questionario_base_url = '/paciente/questionario/'

        # Prefixes permitidos que não são da área do paciente (como estáticos e admin)
        allowed_prefixes_non_patient = ['/media/', '/static/', '/admin/']

        is_patient_area_url = path.startswith('/paciente/')

        # 2. SE NÃO ESTÁ LOGADO:
        if is_patient_area_url or (path not in allowed_paths and not any(
                path.startswith(prefix) for prefix in allowed_prefixes_non_patient)):

            # Checa se os termos foram aceitos na sessão
            if not request.session.get(TERMOS_ACEITOS_KEY, False):

                # --- Lógica para redirecionar para a tela de aceite com o PK (para retorno) ---

                # 2.1: Se a rota for a própria rota de aceite (/ler_termos/ ou /ler_termos/pk/)
                if path.startswith(reverse('narrativa:ler_termos')):
                    return self.get_response(request)

                # 2.2: Se o paciente acessou diretamente uma cena ou questionário (que possui PK)
                if path.startswith(cena_base_url) or path.startswith(questionario_base_url):

                    try:
                        # Extrai o PK (ID) da URL (assumindo que o ID é o penúltimo segmento: /paciente/cena/ID/)
                        parts = path.strip('/').split('/')
                        obj_id = int(parts[-1])  # O ID deve ser o último elemento após o strip('/')

                        # Usa a rota ler_termos_pk para retornar ao fluxo daquela cena/questionário
                        return redirect('narrativa:ler_termos_pk', narrativa_pk=obj_id)
                    except (ValueError, IndexError):
                        # Se não conseguir extrair o ID, cai para o redirecionamento padrão
                        pass  # Continua para a próxima linha

                # 2.3: Para acesso a /paciente/narrativas/ ou rotas sem ID
                return redirect('narrativa:ler_termos')

            # 3. Se os termos foram aceitos, permite o acesso
            return self.get_response(request)

        # 4. Se não está logado e está em uma rota permitida (login, home, termos, estáticos), permite.
        return self.get_response(request)