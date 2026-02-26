from django.db import models
from django.contrib.auth.models import AbstractUser

class Clinica(models.Model):
    PLANOS_CHOICES = [
        ('BASIC', 'Básico'),
        ('PRO', 'Profissional'),
        ('ADVANCED', 'Avançado'),
        ('ENTERPRISE', 'Enterprise'),
    ]

    nome = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, null=True, blank=True)
    logo = models.ImageField(upload_to='logos/', null=True, blank=True)
    assinatura_ativa = models.BooleanField(default=False)

    plano = models.CharField(max_length=20, choices=PLANOS_CHOICES, default='BASIC')
    limite_narrativas = models.IntegerField(default=5)
    limite_respostas_mes = models.IntegerField(default=100)

    stripe_customer_id = models.CharField(max_length=255, null=True, blank=True)
    stripe_subscription_id = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return self.nome

class Usuario(AbstractUser):
    email = models.EmailField(unique=True)
    clinica = models.ForeignKey(Clinica, on_delete=models.SET_NULL, null=True, blank=True)
    is_admin_clinica = models.BooleanField(default=False)
    narrativas_vistas = models.ManyToManyField('Narrativa', blank=True)

    # CORREÇÃO PARA O ERRO E304 (Conflito de acessores reversos)
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='usuario_custom_set',
        blank=True,
        help_text='The groups this user belongs to.',
        verbose_name='groups',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='usuario_custom_permissions_set',
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions',
    )

    def __str__(self):
        return self.username

class Categoria(models.Model):
    nome = models.CharField(max_length=100)
    def __str__(self): return self.nome

class Narrativa(models.Model):
    titulo = models.CharField(max_length=200)
    capa = models.ImageField(upload_to='capas/')
    descricao = models.TextField()
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE)
    visualizacoes = models.IntegerField(default=0)
    clinica = models.ForeignKey(Clinica, on_delete=models.CASCADE)
    def __str__(self): return self.titulo

class Cena(models.Model):
    narrativa = models.ForeignKey(Narrativa, on_delete=models.CASCADE, related_name='cenas')
    titulo = models.CharField(max_length=200)
    conteudo = models.TextField()
    imagem = models.ImageField(upload_to='cenas/', null=True, blank=True)
    video_url = models.URLField(null=True, blank=True)
    ordem = models.IntegerField(default=0)

class Questionario(models.Model):
    cena_associada = models.OneToOneField(Cena, on_delete=models.CASCADE, related_name='questionario')
    titulo = models.CharField(max_length=200)
    cena_destino = models.ForeignKey(Cena, on_delete=models.SET_NULL, null=True, blank=True, related_name='destino_de')

class Pergunta(models.Model):
    questionario = models.ForeignKey(Questionario, on_delete=models.CASCADE, related_name='perguntas')
    texto = models.CharField(max_length=300)
    tipo = models.CharField(max_length=20, choices=[('TEXTO', 'Texto'), ('MULTIPLA_ESCOLHA', 'Múltipla Escolha')])

class Resposta(models.Model):
    pergunta = models.ForeignKey(Pergunta, on_delete=models.CASCADE)
    session_key = models.CharField(max_length=100)
    texto_resposta = models.TextField()
    data_criacao = models.DateTimeField(auto_now_add=True)

class SessaoPaciente(models.Model):
    session_key = models.CharField(max_length=100)
    narrativa_perfil = models.ForeignKey(Narrativa, on_delete=models.CASCADE)
    data_inicio = models.DateTimeField(auto_now_add=True)

class LogVisitaCena(models.Model):
    session_key = models.CharField(max_length=100)
    cena_visitada = models.ForeignKey(Cena, on_delete=models.CASCADE)
    narrativa_associada = models.ForeignKey(Narrativa, on_delete=models.CASCADE)
    data_visita = models.DateTimeField(auto_now_add=True)