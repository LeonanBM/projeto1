from django.contrib import admin
from .models import Pessoa, Verificacao

@admin.register(Pessoa)
class PessoaAdm(admin.ModelAdmin):
    list_display = ('nome', 'imagem', 'encodings', 'total_verificacoes',)

@admin.register(Verificacao)
class VerificacaoAdmin(admin.ModelAdmin):
    list_display = ('pessoa', 'horario',)