# recipes/models.py
from django.db import models

class Verificacao(models.Model):
    pessoa = models.ForeignKey('Pessoa', on_delete=models.CASCADE)
    horario = models.DateTimeField(auto_now_add=True)

class Pessoa(models.Model):
    nome = models.CharField(max_length=100)
    imagem = models.ImageField(upload_to='imagens/')
    encodings = models.BinaryField(null=True, blank=True)

    def __str__(self):
        return self.nome

class CadastroEmAnalise(models.Model):
    nome = models.CharField(max_length=100)
    imagem = models.ImageField(upload_to='cadastro_analise/')
    encodings = models.BinaryField(null=True, blank=True)
    analise_concluida = models.BooleanField(default=False)

class RegistroReconhecimento(models.Model):
    pessoa = models.ForeignKey('Pessoa', on_delete=models.CASCADE)
    horario = models.DateTimeField(auto_now_add=True)