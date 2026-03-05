from django.db import models
from django.contrib.auth.models import AbstractUser


# 1. TABELA DE PREÇOS DO STRIPE (Para a sua Home carregar os planos)
class Plano(models.Model):
    PLANOS_CHOICES = [
        ('BASIC', 'Básico'),
        ('PRO', 'Profissional'),
        ('ADVANCED', 'Avançado'),
        ('ENTERPRISE', 'Enterprise'),
    ]
    nome_exibicao = models.CharField(max_length=100)  # Ex: "Plano Profissional"
    slug_plano = models.CharField(max_length=20, choices=PLANOS_CHOICES, default='BASIC')
    preco = models.DecimalField(max_digits=10, decimal_places=2)
    descricao = models.TextField(help_text="Descrição que aparece no card")
    pid = models.CharField(max_length=255, help_text="O ID do Preço no Dashboard do Stripe (ex: price_123...)")

    limite_narrativas = models.IntegerField(default=5)
    limite_respostas = models.IntegerField(default=100)

    def __str__(self):
        return f"{self.nome_exibicao} - R$ {self.preco}"


# 2. TABELA DA CLÍNICA (O Assinante)
class Clinica(models.Model):
    nome = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, null=True, blank=True)
    logo = models.ImageField(upload_to='logos/', null=True, blank=True)
    assinatura_ativa = models.BooleanField(default=False)

    # Relacionamento com o Plano
    plano_atual = models.ForeignKey(Plano, on_delete=models.SET_NULL, null=True, blank=True)

    # Dados do Stripe
    stripe_customer_id = models.CharField(max_length=255, null=True, blank=True)
    stripe_subscription_id = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return self.nome


# 3. TABELA DE USUÁRIO (Médicos/Admin)
class Usuario(AbstractUser):
    email = models.EmailField(unique=True)
    clinica = models.ForeignKey(Clinica, on_delete=models.SET_NULL, null=True, blank=True)
    is_admin_clinica = models.BooleanField(default=False)
    narrativas_vistas = models.ManyToManyField('Narrativa', blank=True)

    groups = models.ManyToManyField(
        'auth.Group',
        related_name='usuario_custom_set',
        blank=True,
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='usuario_custom_permissions_set',
        blank=True,
    )

    def __str__(self):
        return self.username


# 4. ESTRUTURA DAS NARRATIVAS
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

    def __str__(self): return f"{self.narrativa.titulo} - {self.titulo}"


# 5. QUESTIONÁRIOS E RESPOSTAS
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


# 6. LOGS E SESSÕES DE PACIENTES
class SessaoPaciente(models.Model):
    session_key = models.CharField(max_length=100)
    narrativa_perfil = models.ForeignKey(Narrativa, on_delete=models.CASCADE)
    data_inicio = models.DateTimeField(auto_now_add=True)


class LogVisitaCena(models.Model):
    session_key = models.CharField(max_length=100)
    cena_visitada = models.ForeignKey(Cena, on_delete=models.CASCADE)
    narrativa_associada = models.ForeignKey(Narrativa, on_delete=models.CASCADE)
    data_visita = models.DateTimeField(auto_now_add=True)