from django.db import models
from django.contrib.auth.models import AbstractUser


# ==========================================
# MODELOS DE SAAS E ASSINATURA
# ==========================================

class Plano(models.Model):
    nome_exibicao = models.CharField(max_length=100)
    preco = models.DecimalField(max_digits=10, decimal_places=2)
    descricao = models.TextField()
    pid = models.CharField(max_length=255, help_text="ID do Preço no Stripe")
    limite_narrativas = models.IntegerField(default=5)

    def __str__(self):
        return self.nome_exibicao


class Clinica(models.Model):
    nome = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, null=True, blank=True)
    logo = models.ImageField(upload_to='logos/', null=True, blank=True)
    assinatura_ativa = models.BooleanField(default=False)
    plano_atual = models.ForeignKey(Plano, on_delete=models.SET_NULL, null=True, blank=True)
    stripe_customer_id = models.CharField(max_length=255, null=True, blank=True)
    stripe_subscription_id = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return self.nome


class Usuario(AbstractUser):
    email = models.EmailField(unique=True)
    clinica = models.ForeignKey(Clinica, on_delete=models.SET_NULL, null=True, blank=True)
    is_admin_clinica = models.BooleanField(default=False)

    groups = models.ManyToManyField('auth.Group', related_name='usuario_custom_set', blank=True)
    user_permissions = models.ManyToManyField('auth.Permission', related_name='usuario_custom_permissions_set',
                                              blank=True)


# ==========================================
# MODELOS DA JORNADA CLÍNICA (V1 Preservada)
# ==========================================

class Categoria(models.Model):
    nome = models.CharField(max_length=100)

    def __str__(self):
        return self.nome


class Narrativa(models.Model):
    clinica = models.ForeignKey(Clinica, on_delete=models.CASCADE)
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE)
    titulo = models.CharField(max_length=200)
    thumb = models.ImageField(upload_to='capas/')
    descricao = models.TextField()
    visualizacoes = models.IntegerField(default=0)
    data_criacao = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.titulo


class Cena(models.Model):
    narrativa = models.ForeignKey(Narrativa, on_delete=models.CASCADE, related_name='cenas')
    titulo = models.CharField(max_length=200)
    conteudo_textual = models.TextField(blank=True, null=True)
    imagem = models.ImageField(upload_to='cenas_imagens/', blank=True, null=True)
    video = models.URLField(max_length=500, blank=True, null=True, help_text="Link do YouTube/Vimeo")
    ordem = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.narrativa.titulo} - {self.titulo}"


class Escolha(models.Model):
    cena_origem = models.ForeignKey(Cena, on_delete=models.CASCADE, related_name='escolhas')
    texto_da_opcao = models.CharField(max_length=255)
    cena_destino = models.ForeignKey(Cena, on_delete=models.SET_NULL, null=True, blank=True, related_name='destinos')

    def __str__(self):
        return self.texto_da_opcao


class Questionario(models.Model):
    cena_associada = models.OneToOneField(Cena, on_delete=models.CASCADE, related_name='questionarios')
    titulo = models.CharField(max_length=200)

    def __str__(self):
        return self.titulo


class Pergunta(models.Model):
    TIPOS_RESPOSTA = [
        ('TEXTO', 'Texto Livre'),
        ('ESCALA_5', 'Escala de 1 a 5 Estrelas'),
        ('UNICA_ESCOLHA', 'Única Escolha'),
        ('MULTIPLA_ESCOLHA', 'Múltipla Escolha'),
    ]
    questionario = models.ForeignKey(Questionario, on_delete=models.CASCADE, related_name='perguntas')
    texto_pergunta = models.CharField(max_length=300)
    tipo_resposta = models.CharField(max_length=20, choices=TIPOS_RESPOSTA)

    def __str__(self):
        return self.texto_pergunta


class OpcaoResposta(models.Model):
    pergunta = models.ForeignKey(Pergunta, on_delete=models.CASCADE, related_name='opcoes')
    texto = models.CharField(max_length=200)

    def __str__(self):
        return self.texto


class Resposta(models.Model):
    pergunta = models.ForeignKey(Pergunta, on_delete=models.CASCADE)
    texto_resposta = models.TextField()
    session_key = models.CharField(max_length=100)
    data_criacao = models.DateTimeField(auto_now_add=True)