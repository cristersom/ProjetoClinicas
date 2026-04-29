from django.db import models
from django.utils import timezone
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError

class Plano(models.Model):
    nome = models.CharField(max_length=100)
    descricao_curta = models.CharField(max_length=200, default="Ideal para acompanhamento de pacientes", help_text="Aparece abaixo do nome na tela de vendas.")
    preco = models.DecimalField(max_digits=10, decimal_places=2)
    stripe_product_id = models.CharField(max_length=255, blank=True, null=True)
    stripe_price_id = models.CharField(max_length=255)
    limite_narrativas = models.IntegerField(default=1, help_text="Quantas narrativas ativas a clínica pode ter simultaneamente?")
    limite_pacientes = models.IntegerField(default=5, help_text="Quantos pacientes a clínica pode cadastrar?")
    destaque = models.BooleanField(default=False, help_text="Marque para deixar este plano com visual de 'Recomendado' na tela.")

    def __str__(self):
        return f"{self.nome} - R$ {self.preco}"

class Clinica(models.Model):
    nome = models.CharField(max_length=255)
    logo = models.ImageField(upload_to='logos/', null=True, blank=True)
    assinatura_ativa = models.BooleanField(default=False)
    stripe_customer_id = models.CharField(max_length=255, blank=True, null=True)
    plano = models.ForeignKey(Plano, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.nome

    def atingiu_limite_narrativas(self):
        if not self.plano:
            return True
        return self.narrativas.count() >= self.plano.limite_narrativas

class Usuario(AbstractUser):
    clinica = models.OneToOneField(Clinica, on_delete=models.CASCADE, null=True, blank=True)
    narrativas_vistas = models.ManyToManyField("Narrativa", blank=True)

class Categoria(models.Model):
    titulo = models.CharField(max_length=100, unique=True)
    class Meta:
        verbose_name_plural = "Categorias"
    def __str__(self):
        return self.titulo

class Narrativa(models.Model):
    clinica = models.ForeignKey(Clinica, on_delete=models.CASCADE, related_name="narrativas", null=True)
    titulo = models.CharField(max_length=100)
    thumb = models.ImageField(upload_to='thumb_narrativas')
    descricao = models.TextField(max_length=1000)
    categoria = models.ForeignKey(Categoria, on_delete=models.SET_NULL, null=True, blank=True)
    visualizacoes = models.IntegerField(default=0)
    data_criacao = models.DateTimeField(default=timezone.now)
    cena_inicial = models.ForeignKey('Cena', on_delete=models.SET_NULL, null=True, blank=True, related_name='inicio_narrativa')

    def clean(self):
        if not self.pk and self.clinica:
            if self.clinica.atingiu_limite_narrativas():
                raise ValidationError(f"Sua clínica atingiu o limite de {self.clinica.plano.limite_narrativas} narrativas do plano {self.clinica.plano.nome}. Faça um upgrade para criar mais.")

    def __str__(self):
        return self.titulo

class Cena(models.Model):
    narrativa = models.ForeignKey(Narrativa, related_name='cenas', on_delete=models.CASCADE)
    titulo = models.CharField(max_length=100)
    conteudo_textual = models.TextField(blank=True, null=True)
    imagem = models.ImageField(upload_to='cenas_imagens/', blank=True, null=True)
    video = models.URLField(max_length=200, blank=True, null=True, help_text="Insira o link do vídeo (YouTube, Vimeo, etc.)")

    def __str__(self):
        return f"{self.titulo} ({self.narrativa.titulo})"

class Escolha(models.Model):
    cena_origem = models.ForeignKey(Cena, related_name='escolhas', on_delete=models.CASCADE)
    texto_da_opcao = models.CharField(max_length=255)
    cena_destino = models.ForeignKey(Cena, related_name='destinos', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.texto_da_opcao

class Questionario(models.Model):
    cena_associada = models.ForeignKey(Cena, related_name="questionarios", on_delete=models.CASCADE, null=True, blank=True)
    titulo = models.CharField(max_length=200)
    cena_destino = models.ForeignKey(Cena, related_name="destinos_questionario", on_delete=models.SET_NULL, null=True, blank=True, help_text="Para onde o paciente vai após responder? Se vazio, permanece na mesma cena.")

    def __str__(self):
        return self.titulo

class Pergunta(models.Model):
    TIPOS_RESPOSTA = (
        ('TEXTO', 'Texto Livre'),
        ('ESCALA', 'Escala (1 a 5)'),
        ('UNICA_ESCOLHA', 'Única Escolha'),
        ('MULTIPLA_ESCOLHA', 'Múltipla Escolha'),
    )
    questionario = models.ForeignKey(Questionario, related_name="perguntas", on_delete=models.CASCADE)
    texto_pergunta = models.CharField(max_length=500)
    tipo_resposta = models.CharField(max_length=20, choices=TIPOS_RESPOSTA)

    def __str__(self):
        return self.texto_pergunta

class OpcaoResposta(models.Model):
    pergunta = models.ForeignKey(Pergunta, related_name="opcoes", on_delete=models.CASCADE)
    texto = models.CharField(max_length=200)

    def __str__(self):
        return self.texto

class Resposta(models.Model):
    pergunta = models.ForeignKey(Pergunta, related_name="respostas", on_delete=models.CASCADE)
    session_key = models.CharField(max_length=40, help_text="ID da sessão do paciente")
    texto_resposta = models.TextField()
    data_resposta = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Resposta para '{self.pergunta.texto_pergunta}'"

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
        return f"Sessão {self.session_key[:8]}... visitou '{self.cena_visitada.titulo}' em {self.timestamp.strftime('%d/%m/%Y %H:%M')}"

    class Meta:
        ordering = ['session_key', 'timestamp']

class ConfiguracaoClinica(models.Model):
    logo = models.ImageField(upload_to='logos/', null=True, blank=True, help_text="Logo global do sistema (se aplicável)")