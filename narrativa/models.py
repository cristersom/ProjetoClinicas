from django.db import models
from django.utils import timezone
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError


# ==========================================
# MODELOS DE SAAS E ASSINATURA
# ==========================================
class Plano(models.Model):
    nome = models.CharField(max_length=100)
    descricao_curta = models.CharField(max_length=200, default="Ideal para acompanhamento de pacientes",
                                       help_text="Aparece abaixo do nome na tela de vendas.")
    preco = models.DecimalField(max_digits=10, decimal_places=2)
    stripe_product_id = models.CharField(max_length=255, blank=True, null=True)
    stripe_price_id = models.CharField(max_length=255)

    # NOVOS CAMPOS PARA CONTROLE DO SaaS E VISUAL
    limite_narrativas = models.IntegerField(default=1,
                                            help_text="Quantas narrativas ativas a clínica pode ter simultaneamente?")
    limite_pacientes = models.IntegerField(default=5, help_text="Quantos pacientes a clínica pode cadastrar?")
    destaque = models.BooleanField(default=False,
                                   help_text="Marque para deixar este plano com visual de 'Recomendado' na tela.")

    def __str__(self):
        return f"{self.nome} - R$ {self.preco}"


# ---> NOVO: Armazena o pagamento antes da conta existir para sincronizar o onboarding
class PagamentoPendente(models.Model):
    email = models.EmailField(unique=True, help_text="E-mail usado no checkout do Stripe")
    plano = models.ForeignKey(Plano, on_delete=models.CASCADE)
    stripe_customer_id = models.CharField(max_length=255, blank=True, null=True)
    data_pagamento = models.DateTimeField(auto_now_add=True)
    utilizado = models.BooleanField(default=False, help_text="Marca como True após o usuário criar a conta.")

    def __str__(self):
        return f"Pagamento Pendente: {self.email} ({self.plano.nome})"


class Clinica(models.Model):
    nome = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, null=True, blank=True)
    logo = models.ImageField(upload_to='logos/', null=True, blank=True,
                             help_text="Logo da clínica. Recomendado: 250x45 px.")
    assinatura_ativa = models.BooleanField(default=False)
    plano_atual = models.ForeignKey(Plano, on_delete=models.SET_NULL, null=True, blank=True)
    stripe_customer_id = models.CharField(max_length=255, null=True, blank=True)
    stripe_subscription_id = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return self.nome

    # ---> NOVO: Checa se a clínica já bateu o limite do plano contratado
    def atingiu_limite_narrativas(self):
        if not self.plano_atual:
            return True
        return self.narrativa_set.count() >= self.plano_atual.limite_narrativas


class Usuario(AbstractUser):
    email = models.EmailField(unique=True)
    clinica = models.ForeignKey(Clinica, on_delete=models.SET_NULL, null=True, blank=True)
    is_admin_clinica = models.BooleanField(default=False)
    narrativas_vistas = models.ManyToManyField("Narrativa", blank=True)


# ==========================================
# MODELOS DA JORNADA CLÍNICA
# ==========================================

class Categoria(models.Model):
    titulo = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.titulo

    class Meta:
        verbose_name_plural = "Categorias"


class Narrativa(models.Model):
    clinica = models.ForeignKey(Clinica, on_delete=models.CASCADE, null=True, blank=True)
    categoria = models.ForeignKey(Categoria, on_delete=models.SET_NULL, null=True, blank=True)
    titulo = models.CharField(max_length=100)
    thumb = models.ImageField(upload_to='thumb_narrativas', null=True, blank=True,
                              help_text="Opcional. Imagem de capa.")
    descricao = models.TextField(max_length=1000, null=True, blank=True, help_text="Opcional.")
    visualizacoes = models.IntegerField(default=0)
    data_criacao = models.DateTimeField(default=timezone.now)
    cena_inicial = models.ForeignKey('Cena', on_delete=models.SET_NULL, null=True, blank=True, related_name='+')

    # ---> NOVO: Bloqueia a criação de novas narrativas se o limite do plano foi atingido
    def clean(self):
        if not self.pk and self.clinica:
            if self.clinica.atingiu_limite_narrativas():
                raise ValidationError(f"Sua clínica atingiu o limite de {self.clinica.plano_atual.limite_narrativas} narrativas do plano {self.clinica.plano_atual.nome}. Faça um upgrade para criar mais.")

    def __str__(self):
        return self.titulo


class Cena(models.Model):
    narrativa = models.ForeignKey("Narrativa", related_name="cenas", on_delete=models.CASCADE, null=True, blank=True,
                                  help_text="Lembrete: Vincule a uma narrativa para exibi-la.")
    titulo = models.CharField(max_length=100, help_text="Título interno para identificar a cena")
    conteudo_textual = models.TextField(blank=True, null=True, help_text="Texto principal da cena.")
    imagem = models.ImageField(upload_to='imagem_cenas', blank=True, null=True, help_text="Imagem de apoio.")
    video = models.URLField(blank=True, null=True, help_text="Link do vídeo (opcional).")
    ordem = models.IntegerField(default=0)

    def __str__(self):
        if self.narrativa:
            return f"{self.narrativa.titulo} - {self.titulo}"
        return f"[Solta] - {self.titulo}"


class Escolha(models.Model):
    cena_origem = models.ForeignKey(Cena, related_name="escolhas", on_delete=models.CASCADE)
    texto_da_opcao = models.CharField(max_length=255)
    cena_destino = models.ForeignKey(Cena, on_delete=models.SET_NULL, null=True, blank=True,
                                     related_name='cenas_de_destino')

    def __str__(self):
        destino = self.cena_destino.titulo if self.cena_destino else 'Fim da Jornada'
        return f"Opção em '{self.cena_origem.titulo}': levar para '{destino}'"


class Questionario(models.Model):
    cena_associada = models.ForeignKey('Cena', related_name="questionarios", on_delete=models.SET_NULL, null=True,
                                       blank=True, help_text="Lembrete: Vincule a uma cena.")
    titulo = models.CharField(max_length=200, help_text="Título do questionário.")
    cena_destino = models.ForeignKey('Cena', on_delete=models.SET_NULL, null=True, blank=True,
                                     related_name='questionarios_de_origem')

    def __str__(self): return self.titulo


class Pergunta(models.Model):
    TIPOS_RESPOSTA = (("TEXTO", "Texto Livre"), ("UNICA_ESCOLHA", "Múltipla Escolha (apenas uma resposta)"),
                      ("MULTIPLA_ESCOLHA", "Múltipla Escolha (várias respostas)"),
                      ("ESCALA_5", "Escala de Satisfação (1 a 5)"))
    questionario = models.ForeignKey(Questionario, related_name="perguntas", on_delete=models.CASCADE)
    texto_pergunta = models.CharField(max_length=500)
    tipo_resposta = models.CharField(max_length=20, choices=TIPOS_RESPOSTA)

    def __str__(self): return f"{self.questionario.titulo} - {self.texto_pergunta}"


class OpcaoResposta(models.Model):
    pergunta = models.ForeignKey(Pergunta, related_name="opcoes", on_delete=models.CASCADE)
    texto = models.CharField(max_length=200)

    def __str__(self): return self.texto


class Resposta(models.Model):
    pergunta = models.ForeignKey(Pergunta, related_name="respostas", on_delete=models.CASCADE)
    session_key = models.CharField(max_length=40, help_text="ID da sessão do paciente")
    texto_resposta = models.TextField()
    data_resposta = models.DateTimeField(default=timezone.now)

    def __str__(self): return f"Resposta para '{self.pergunta.texto_pergunta}'"


class SessaoPaciente(models.Model):
    session_key = models.CharField(max_length=40, unique=True)
    narrativa_perfil = models.ForeignKey(Narrativa, on_delete=models.SET_NULL, null=True, blank=True)
    data_criacao = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        perfil = self.narrativa_perfil.titulo if self.narrativa_perfil else 'Não definido'
        return f"Sessão {self.session_key[:8]}... | Perfil: {perfil}"


class LogVisitaCena(models.Model):
    session_key = models.CharField(max_length=40, db_index=True)
    cena_visitada = models.ForeignKey(Cena, on_delete=models.CASCADE, related_name="visitas")
    timestamp = models.DateTimeField(auto_now_add=True)
    narrativa_associada = models.ForeignKey(Narrativa, on_delete=models.CASCADE, related_name="logs_visita", null=True)

    def __str__(self):
        return f"Sessão {self.session_key[:8]}... visitou '{self.cena_visitada.titulo}'"

    class Meta:
        ordering = ['session_key', 'timestamp']