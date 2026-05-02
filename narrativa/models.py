from django.db import models
from django.utils import timezone
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db.models.signals import post_delete
from django.dispatch import receiver

class Plano(models.Model):
    nome = models.CharField(max_length=100)
    descricao_curta = models.CharField(max_length=200, default="Ideal para acompanhamento de pacientes")
    preco = models.DecimalField(max_digits=10, decimal_places=2)
    stripe_product_id = models.CharField(max_length=255, blank=True, null=True)
    stripe_price_id = models.CharField(max_length=255)
    limite_narrativas = models.IntegerField(default=1)
    limite_pacientes = models.IntegerField(default=5)
    destaque = models.BooleanField(default=False)

    def __str__(self): return f"{self.nome} - R$ {self.preco}"

class PagamentoPendente(models.Model):
    email = models.EmailField(unique=True)
    plano = models.ForeignKey(Plano, on_delete=models.CASCADE)
    stripe_customer_id = models.CharField(max_length=255, blank=True, null=True)
    data_pagamento = models.DateTimeField(auto_now_add=True)
    utilizado = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Pagamento Pendente"
        verbose_name_plural = "Pagamentos Pendentes"

    def __str__(self): return f"Pagamento Pendente: {self.email}"

class Clinica(models.Model):
    nome = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, null=True, blank=True)
    logo = models.ImageField(upload_to='logos/', null=True, blank=True)
    assinatura_ativa = models.BooleanField(default=False)
    plano_atual = models.ForeignKey(Plano, on_delete=models.SET_NULL, null=True, blank=True)
    stripe_customer_id = models.CharField(max_length=255, null=True, blank=True)
    stripe_subscription_id = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self): return self.nome

    def atingiu_limite_narrativas(self):
        if not self.assinatura_ativa or not self.plano_atual:
            return True
        return self.narrativa_set.count() >= self.plano_atual.limite_narrativas

class Usuario(AbstractUser):
    email = models.EmailField(unique=True)
    clinica = models.ForeignKey(Clinica, on_delete=models.SET_NULL, null=True, blank=True)
    is_admin_clinica = models.BooleanField(default=False)
    narrativas_vistas = models.ManyToManyField("Narrativa", blank=True)

class Categoria(models.Model):
    titulo = models.CharField(max_length=100, unique=True)
    def __str__(self): return self.titulo
    class Meta: verbose_name_plural = "Categorias"

class Narrativa(models.Model):
    clinica = models.ForeignKey(Clinica, on_delete=models.CASCADE, null=True, blank=True)
    categoria = models.ForeignKey(Categoria, on_delete=models.SET_NULL, null=True, blank=True)
    titulo = models.CharField(max_length=100)
    thumb = models.ImageField(upload_to='thumb_narrativas', null=True, blank=True)
    descricao = models.TextField(max_length=1000, null=True, blank=True)
    visualizacoes = models.IntegerField(default=0)
    data_criacao = models.DateTimeField(default=timezone.now)
    cena_inicial = models.ForeignKey('Cena', on_delete=models.SET_NULL, null=True, blank=True, related_name='+')

    def clean(self):
        # TRAVA BLINDADA NO BANCO DE DADOS
        if self.clinica:
            if not self.clinica.assinatura_ativa:
                raise ValidationError("A assinatura desta clínica está inativa ou foi cancelada.")
            if not self.pk and self.clinica.atingiu_limite_narrativas():
                raise ValidationError("Sua clínica atingiu o limite de narrativas do plano.")

    def __str__(self): return self.titulo

class Cena(models.Model):
    narrativa = models.ForeignKey("Narrativa", related_name="cenas", on_delete=models.CASCADE, null=True, blank=True)
    titulo = models.CharField(max_length=100)
    conteudo_textual = models.TextField(blank=True, null=True)
    imagem = models.ImageField(upload_to='imagem_cenas', blank=True, null=True)
    video = models.URLField(blank=True, null=True)
    ordem = models.IntegerField(default=0)
    def __str__(self): return f"{self.narrativa.titulo} - {self.titulo}" if self.narrativa else f"[Solta] - {self.titulo}"

class Escolha(models.Model):
    cena_origem = models.ForeignKey(Cena, related_name="escolhas", on_delete=models.CASCADE)
    texto_da_opcao = models.CharField(max_length=255)
    cena_destino = models.ForeignKey(Cena, on_delete=models.SET_NULL, null=True, blank=True, related_name='cenas_de_destino')
    def __str__(self): return f"Opção em '{self.cena_origem.titulo}'"

class Questionario(models.Model):
    cena_associada = models.ForeignKey('Cena', related_name="questionarios", on_delete=models.SET_NULL, null=True, blank=True)
    titulo = models.CharField(max_length=200)
    cena_destino = models.ForeignKey('Cena', on_delete=models.SET_NULL, null=True, blank=True, related_name='questionarios_de_origem')
    def __str__(self): return self.titulo

class Pergunta(models.Model):
    TIPOS_RESPOSTA = (("TEXTO", "Texto Livre"), ("UNICA_ESCOLHA", "Múltipla Escolha"), ("MULTIPLA_ESCOLHA", "Múltipla Múltipla"), ("ESCALA_5", "Escala (1-5)"))
    questionario = models.ForeignKey(Questionario, related_name="perguntas", on_delete=models.CASCADE)
    texto_pergunta = models.CharField(max_length=500)
    tipo_resposta = models.CharField(max_length=20, choices=TIPOS_RESPOSTA)
    def __str__(self): return self.texto_pergunta

class OpcaoResposta(models.Model):
    pergunta = models.ForeignKey(Pergunta, related_name="opcoes", on_delete=models.CASCADE)
    texto = models.CharField(max_length=200)
    def __str__(self): return self.texto

class Resposta(models.Model):
    pergunta = models.ForeignKey(Pergunta, related_name="respostas", on_delete=models.CASCADE)
    session_key = models.CharField(max_length=40)
    texto_resposta = models.TextField()
    data_resposta = models.DateTimeField(default=timezone.now)

class SessaoPaciente(models.Model):
    session_key = models.CharField(max_length=40, unique=True)
    narrativa_perfil = models.ForeignKey(Narrativa, on_delete=models.SET_NULL, null=True, blank=True)
    data_criacao = models.DateTimeField(auto_now_add=True)

class LogVisitaCena(models.Model):
    session_key = models.CharField(max_length=40, db_index=True)
    cena_visitada = models.ForeignKey(Cena, on_delete=models.CASCADE, related_name="visitas")
    timestamp = models.DateTimeField(auto_now_add=True)
    narrativa_associada = models.ForeignKey(Narrativa, on_delete=models.CASCADE, related_name="logs_visita", null=True)
    class Meta: ordering = ['session_key', 'timestamp']

class ConfiguracaoClinica(models.Model):
    logo = models.ImageField(upload_to='logos/', null=True, blank=True)

@receiver(post_delete, sender=Usuario)
def limpar_dados_usuario_deletado(sender, instance, **kwargs):
    if hasattr(instance, 'clinica') and instance.clinica:
        instance.clinica.delete()