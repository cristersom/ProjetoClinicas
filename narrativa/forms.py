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

    def clean_email(self):
        email = self.cleaned_data.get('email')
        user = Usuario.objects.filter(email=email).first()
        if user and user.has_usable_password():
            raise forms.ValidationError("Este e-mail já possui um cadastro completo. Faça login.")
        return email

    def save(self, commit=True):
        email = self.cleaned_data['email']
        user = Usuario.objects.filter(email=email).first()

        if user:
            user.username = self.cleaned_data['username']
            if user.clinica:
                user.clinica.nome = self.cleaned_data['nome_clinica']
                user.clinica.save()
        else:
            user = super().save(commit=False)
            user.clinica = Clinica.objects.create(nome=self.cleaned_data['nome_clinica'], assinatura_ativa=False)

        # CRÍTICO: is_staff=True permite que ele logue no painel administrativo!
        user.set_password(self.cleaned_data['senha1'])
        user.is_admin_clinica = True
        user.is_staff = True

        if commit:
            user.save()
        return user