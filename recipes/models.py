# recipes/models.py
from django.db import models

class Pessoa(models.Model):
    nome = models.CharField(max_length=100)
    imagem = models.ImageField(upload_to='imagens/')
    encodings = models.BinaryField(null=True, blank=True)

class CadastroEmAnalise(models.Model):
    nome = models.CharField(max_length=100)
    imagem = models.ImageField(upload_to='cadastro_analise/')
    encodings = models.BinaryField(null=True, blank=True)
    analise_concluida = models.BooleanField(default=False)
