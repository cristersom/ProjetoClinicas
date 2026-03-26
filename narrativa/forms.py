from django import forms
from django.contrib.auth import get_user_model
from .models import Clinica

Usuario = get_user_model()


class CadastroForm(forms.ModelForm):
    nome_clinica = forms.CharField(max_length=100, label='Nome da Clínica/Consultório', required=True)
    senha1 = forms.CharField(widget=forms.PasswordInput, label='Senha')
    senha2 = forms.CharField(widget=forms.PasswordInput, label='Confirme a Senha')

    class Meta:
        model = Usuario
        fields = ['username', 'email']
        labels = {
            'username': 'Nome de Usuário (Login)',
            'email': 'E-mail principal',
        }

    def clean_senha2(self):
        senha1 = self.cleaned_data.get('senha1')
        senha2 = self.cleaned_data.get('senha2')
        if senha1 and senha2 and senha1 != senha2:
            raise forms.ValidationError("As senhas não coincidem. Digite novamente.")
        return senha2

    def save(self, commit=True):
        # 1. Salva o usuário primeiro com a senha criptografada
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['senha1'])
        user.is_admin_clinica = True  # Marca como dono da clínica

        if commit:
            user.save()
            # 2. Cria a clínica zerada (sem assinatura ativa para forçar o pagamento)
            clinica = Clinica.objects.create(
                nome=self.cleaned_data['nome_clinica'],
                assinatura_ativa=False
            )
            # 3. Vincula a clínica ao usuário
            user.clinica = clinica
            user.save()

        return user