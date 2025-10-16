from django.db import models
from django.utils import timezone
from django.contrib.auth.models import AbstractUser

LISTA_CATEGORIAS = (
    ("BOASVINDAS", "Boas vindas"),
    ("TRATAMENTO", "Tratamento"),
    ("ACOMPANHAMENTO", "Acompanhamento"),
    ("REVISÃO", "Revisão"),
    ("ENCERRAMENTO", "Encerramento"),
    ("OUTROS", "Outros"),
)

class Narrativa(models.Model):
    titulo = models.CharField(max_length=100)
    thumb = models.ImageField(upload_to='thumb_narrativas')
    descricao = models.TextField(max_length=1000)
    categoria = models.CharField(max_length=15, choices=LISTA_CATEGORIAS)
    visualizacoes = models.IntegerField(default=0)
    data_criacao = models.DateTimeField(default=timezone.now)
    cena_inicial = models.ForeignKey(
        'Cena',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='+'
    )

    def __str__(self):
        return self.titulo

class Cena(models.Model):
    narrativa = models.ForeignKey("Narrativa", related_name="cenas", on_delete=models.CASCADE)
    titulo = models.CharField(max_length=100, help_text="Título interno para identificar a cena (ex: 'Cena de Boas Vindas')")
    conteudo_textual = models.TextField(blank=True, null=True, help_text="Texto principal que aparecerá na cena.")
    imagem = models.ImageField(upload_to='imagem_cenas', blank=True, null=True, help_text="Imagem de apoio para a cena.")
    video = models.URLField(blank=True, null=True, help_text="Link do vídeo para a cena (opcional).")

    def __str__(self):
        return self.narrativa.titulo + " - " + self.titulo

class Escolha(models.Model):
    cena_origem = models.ForeignKey(Cena, related_name="escolhas", on_delete=models.CASCADE)
    texto_da_opcao = models.CharField(max_length=255)
    cena_destino = models.ForeignKey(
        Cena,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cenas_de_destino'
    )

    def __str__(self):
        destino = self.cena_destino.titulo if self.cena_destino else 'Fim da Jornada'
        return f"Opção em '{self.cena_origem.titulo}': levar para '{destino}'"

class Questionario(models.Model):
    cena_associada = models.ForeignKey(
        'Cena',
        related_name="questionarios",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Opcional: cena ao final da qual este questionário será exibido."
    )
    titulo = models.CharField(max_length=200, help_text="Título do questionário (ex: 'Pesquisa de Satisfação')")
    # O campo 'cena_destino' foi removido daqui, conforme sua solicitação.

    def __str__(self):
        return self.titulo

class Pergunta(models.Model):
    TIPOS_RESPOSTA = (
        ("TEXTO", "Texto Livre"),
        ("UNICA_ESCOLHA", "Múltipla Escolha (apenas uma resposta)"),
        ("MULTIPLA_ESCOLHA", "Múltipla Escolha (várias respostas)"),
        ("ESCALA_5", "Escala de Satisfação (1 a 5)"),
    )
    questionario = models.ForeignKey(Questionario, related_name="perguntas", on_delete=models.CASCADE)
    texto_pergunta = models.CharField(max_length=500)
    tipo_resposta = models.CharField(max_length=20, choices=TIPOS_RESPOSTA)
    # O campo 'opcoes_resposta' foi removido daqui.

    def __str__(self):
        return f"{self.questionario.titulo} - {self.texto_pergunta}"

class OpcaoResposta(models.Model):
    pergunta = models.ForeignKey(Pergunta, related_name="opcoes", on_delete=models.CASCADE)
    texto = models.CharField(max_length=200)

    def __str__(self):
        return self.texto

class Resposta(models.Model):
    pergunta = models.ForeignKey(Pergunta, related_name="respostas", on_delete=models.CASCADE)
    session_key = models.CharField(max_length=40, help_text="ID da sessão do paciente anônimo")
    texto_resposta = models.TextField()
    data_resposta = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Resposta para '{self.pergunta.texto_pergunta}' (Sessão: {self.session_key[:6]}...)"

class SessaoPaciente(models.Model):
    session_key = models.CharField(max_length=40, unique=True)
    narrativa_perfil = models.ForeignKey(Narrativa, on_delete=models.SET_NULL, null=True, blank=True)
    data_criacao = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        perfil = self.narrativa_perfil.titulo if self.narrativa_perfil else 'Não definido'
        return f"Sessão {self.session_key[:8]}... | Perfil: {perfil}"

class Usuario(AbstractUser):
    narrativas_vistas = models.ManyToManyField("Narrativa", blank=True)