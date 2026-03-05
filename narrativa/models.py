from django.db import models
from django.contrib.auth.models import AbstractUser

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
    assinatura_ativa = models.BooleanField(default=False)
    plano_atual = models.ForeignKey(Plano, on_delete=models.SET_NULL, null=True, blank=True)
    stripe_customer_id = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return self.nome

class Usuario(AbstractUser):
    email = models.EmailField(unique=True)
    clinica = models.ForeignKey(Clinica, on_delete=models.SET_NULL, null=True, blank=True)
    is_admin_clinica = models.BooleanField(default=False)

    groups = models.ManyToManyField('auth.Group', related_name='usuario_custom_set', blank=True)
    user_permissions = models.ManyToManyField('auth.Permission', related_name='usuario_custom_permissions_set', blank=True)

# --- Seus modelos originais de Narrativas mantidos abaixo ---
class Categoria(models.Model):
    nome = models.CharField(max_length=100)
    def __str__(self): return self.nome

class Narrativa(models.Model):
    titulo = models.CharField(max_length=200)
    capa = models.ImageField(upload_to='capas/')
    descricao = models.TextField()
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE)
    clinica = models.ForeignKey(Clinica, on_delete=models.CASCADE)
    def __str__(self): return self.titulo

class Cena(models.Model):
    narrativa = models.ForeignKey(Narrativa, on_delete=models.CASCADE, related_name='cenas')
    titulo = models.CharField(max_length=200)
    conteudo = models.TextField()
    ordem = models.IntegerField(default=0)

class Questionario(models.Model):
    cena_associada = models.OneToOneField(Cena, on_delete=models.CASCADE, related_name='questionario')
    titulo = models.CharField(max_length=200)

class Pergunta(models.Model):
    questionario = models.ForeignKey(Questionario, on_delete=models.CASCADE, related_name='perguntas')
    texto = models.CharField(max_length=300)
    tipo = models.CharField(max_length=20, choices=[('TEXTO', 'Texto'), ('MULTIPLA_ESCOLHA', 'Múltipla Escolha')])

class Resposta(models.Model):
    pergunta = models.ForeignKey(Pergunta, on_delete=models.CASCADE)
    texto_resposta = models.TextField()
    data_criacao = models.DateTimeField(auto_now_add=True)