from django import forms
from .models import Pergunta

# Obtém as opções originais do model, incluindo a tupla interna se houver
# (Ex: (("TEXTO", "Texto Livre"), ...) -> [("TEXTO", "Texto Livre"), ...]
PERGUNTA_TIPO_CHOICES = list(Pergunta.TIPOS_RESPOSTA)


class PerguntaAdminForm(forms.ModelForm):
    # Adiciona a opção vazia manualmente no início da lista
    tipo_resposta = forms.ChoiceField(
        choices=[('', 'Selecione o tipo')] + PERGUNTA_TIPO_CHOICES,  # Adiciona a opção vazia
        required=True  # Mantém como obrigatório
    )

    texto_pergunta = forms.CharField(
        widget=forms.TextInput(attrs={  # Usamos TextInput, mas poderia ser Textarea se preferir campo maior
            'placeholder': 'Digite o texto da pergunta aqui...',
            'style': 'width: 90%;'  # Ajusta a largura se necessário
        }),
        required=True
    )

    class Meta:
        model = Pergunta
        fields = '__all__'