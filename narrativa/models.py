from django.db import models
from django.utils import timezone
from django.contrib.auth.models import AbstractUser

# Create your models here.
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

    def __str__(self):
        return self.titulo

# Criar  Cenas

# Criar Cenas interativas (MODIFICADO)
class Cena(models.Model):
    narrativa = models.ForeignKey("Narrativa", related_name="cenas", on_delete=models.CASCADE)
    titulo = models.CharField(max_length=100, help_text="Título interno para identificar a cena (ex: 'Cena de Boas Vindas')")
    conteudo_textual = models.TextField(blank=True, null=True, help_text="Texto principal que aparecerá na cena.")
    imagem = models.ImageField(upload_to='imagem_cenas', blank=True, null=True, help_text="Imagem de apoio para a cena.")
    video = models.URLField(blank=True, null=True, help_text="Link do vídeo para a cena (opcional).")

    def __str__(self):
        return self.narrativa.titulo + " - " + self.titulo

class Usuario(AbstractUser):
    narrativas_vistas = models.ManyToManyField("Narrativa")