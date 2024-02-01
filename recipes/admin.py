# recipes/admin.py
from django.contrib import admin
from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect
from django.urls import path
from .models import Pessoa, CadastroEmAnalise, RegistroReconhecimento
from django.utils.safestring import mark_safe
from django.urls import reverse
from django.utils.html import format_html

@admin.register(Pessoa)
class PessoaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'imagem', 'encodings',)

@admin.register(CadastroEmAnalise)
class CadastroEmAnaliseAdmin(admin.ModelAdmin):
    list_display = ('nome', 'imagem', 'analise_concluida', 'acoes')

    def acoes(self, obj):
        try:
            url = reverse('admin:move-para-pessoas', args=[obj.id])
        except:
            return ''
        return format_html('<a href="{}">Mover para Pessoas</a>', url)

    acoes.short_description = 'Ações'

    def move_para_pessoas(self, request, cadastro_id):
        cadastro_analise = get_object_or_404(CadastroEmAnalise, pk=cadastro_id)

        # Adicione aqui a lógica para mover para a tabela de pessoas
        pessoa = Pessoa.objects.create(
            nome=cadastro_analise.nome,
            imagem=cadastro_analise.imagem,
            encodings=cadastro_analise.encodings
        )

        # Marque a análise como concluída
        cadastro_analise.analise_concluida = True
        cadastro_analise.save()

        # Redirecione de volta para a lista de CadastroEmAnalise
        return HttpResponseRedirect(reverse('admin:recipes_cadastroemanalise_changelist'))

    move_para_pessoas.short_description = 'Mover para Pessoas'

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<path:cadastro_id>/move-para-pessoas/', self.admin_site.admin_view(self.move_para_pessoas), name='move-para-pessoas'),
        ]
        return custom_urls + urls
    
    
@admin.register(RegistroReconhecimento)
class RegistroReconhecimentoAdmin(admin.ModelAdmin):
    list_display = ['pessoa', 'horario']