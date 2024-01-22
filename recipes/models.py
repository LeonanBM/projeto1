from django.db import models

class Pessoa(models.Model):
    nome = models.CharField(max_length=100)
    imagem = models.ImageField(upload_to='imagens/')
    encodings = models.BinaryField(null=True, blank=True)