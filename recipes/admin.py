from django.contrib import admin
from .models import Pessoa

@admin.register(Pessoa)
class PessoaAdm(admin.ModelAdmin):
    list_display = ('nome', 'imagem', 'encodings',)