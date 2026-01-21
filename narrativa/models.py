from django.db import models
from django.utils import timezone
from django.contrib.auth.models import AbstractUser


class Clinica(models.Model):
    nome = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, help_text="Identificador na URL (ex: clinica-pax)")
    logo = models.ImageField(upload_to='logos/', null=True, blank=True)

    # Integração com Stripe (Vendas)
    stripe_customer_id = models.CharField(max_length=255, blank=True, null=True)
    assinatura_ativa = models.BooleanField(default=False)
    data_expiracao = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.nome

    class Meta:
        verbose_name = "Clínica"
        verbose_name_plural = "Clínicas"


class Categoria(models.Model):
    clinica = models.ForeignKey(Clinica, on_delete=models.CASCADE, related_name='categorias', null=True)
    titulo = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.titulo} ({self.clinica.nome if self.clinica else 'Global'})"

    class Meta:
        verbose_name_plural = "Categorias"


class Narrativa(models.Model):
    clinica = models.ForeignKey(Clinica, on_delete=models.CASCADE, related_name='narrativas', null=True)
    titulo = models.CharField(max_length=100)
    thumb = models.ImageField(upload_to='thumb_narrativas')
    descricao = models.TextField(max_length=1000)
    categoria = models.ForeignKey(Categoria, on_delete=models.SET_NULL, null=True, blank=True)
    visualizacoes = models.IntegerField(default=0)
    data_criacao = models.DateTimeField(default=timezone.now)
    cena_inicial = models.ForeignKey('Cena', on_delete=models.SET_NULL, null=True, blank=True, related_name='+')

    def __str__(self):
        return f"{self.titulo} - {self.clinica.nome if self.clinica else 'N/A'}"


class Cena(models.Model):
    narrativa = models.ForeignKey("Narrativa", related_name="cenas", on_delete=models.CASCADE)
    titulo = models.CharField(max_length=100)
    conteudo_textual = models.TextField(blank=True, null=True)
    imagem = models.ImageField(upload_to='imagem_cenas', blank=True, null=True)
    video = models.URLField(blank=True, null=True)

    def __str__(self):
        return f"{self.narrativa.titulo} - {self.titulo}"


class Escolha(models.Model):
    cena_origem = models.ForeignKey(Cena, related_name="escolhas", on_delete=models.CASCADE)
    texto_da_opcao = models.CharField(max_length=255)
    cena_destino = models.ForeignKey(Cena, on_delete=models.SET_NULL, null=True, blank=True,
                                     related_name='cenas_de_destino')


class Questionario(models.Model):
    cena_associada = models.ForeignKey('Cena', related_name="questionarios", on_delete=models.SET_NULL, null=True,
                                       blank=True)
    titulo = models.CharField(max_length=200)
    cena_destino = models.ForeignKey('Cena', on_delete=models.SET_NULL, null=True, blank=True,
                                     related_name='questionarios_de_origem')


class Pergunta(models.Model):
    TIPOS_RESPOSTA = (("TEXTO", "Texto Livre"), ("UNICA_ESCOLHA", "Múltipla Escolha (uma)"),
                      ("MULTIPLA_ESCOLHA", "Múltipla Escolha (várias)"), ("ESCALA_5", "Escala 1 a 5"))
    questionario = models.ForeignKey(Questionario, related_name="perguntas", on_delete=models.CASCADE)
    texto_pergunta = models.CharField(max_length=500)
    tipo_resposta = models.CharField(max_length=20, choices=TIPOS_RESPOSTA)


class OpcaoResposta(models.Model):
    pergunta = models.ForeignKey(Pergunta, related_name="opcoes", on_delete=models.CASCADE)
    texto = models.CharField(max_length=200)


class Resposta(models.Model):
    pergunta = models.ForeignKey(Pergunta, related_name="respostas", on_delete=models.CASCADE)
    session_key = models.CharField(max_length=40)
    texto_resposta = models.TextField()
    data_resposta = models.DateTimeField(default=timezone.now)


class SessaoPaciente(models.Model):
    session_key = models.CharField(max_length=40, unique=True)
    narrativa_perfil = models.ForeignKey(Narrativa, on_delete=models.SET_NULL, null=True, blank=True)
    data_criacao = models.DateTimeField(auto_now_add=True)


class Usuario(AbstractUser):
    clinica = models.ForeignKey(Clinica, on_delete=models.SET_NULL, null=True, blank=True, related_name='usuarios')
    is_admin_clinica = models.BooleanField(default=False)
    narrativas_vistas = models.ManyToManyField("Narrativa", blank=True)


class LogVisitaCena(models.Model):
    session_key = models.CharField(max_length=40, db_index=True)
    cena_visitada = models.ForeignKey(Cena, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    narrativa_associada = models.ForeignKey(Narrativa, on_delete=models.CASCADE, null=True)