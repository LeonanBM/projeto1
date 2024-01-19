# models.py
from django.db import models
import datetime

class Verificacao(models.Model):
    pessoa = models.ForeignKey('Pessoa', on_delete=models.CASCADE)
    horario = models.DateTimeField(auto_now_add=True)

class Pessoa(models.Model):
    nome = models.CharField(max_length=100)
    imagem = models.ImageField(upload_to='imagens/')
    encodings = models.BinaryField(null=True, blank=True)
    total_verificacoes = models.IntegerField(default=0)

    def __str__(self):
        return self.nome

    def registrar_verificacao(self):
        Verificacao.objects.create(pessoa=self)  # Corrigido aqui