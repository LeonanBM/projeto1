# views.py
from django.shortcuts import render, redirect
from .models import Pessoa,Verificacao
import face_recognition
from django.http import HttpResponse
import numpy as np
from django.views.generic import TemplateView,CreateView,View,ListView,UpdateView,DeleteView
import io
from django.http import JsonResponse
from datetime import datetime
from .form import ImageUploadForm
import cv2
import os

class Test(View):
    template_name = 'index.html'

    @staticmethod
    def recognize_face(uploaded_image):
        people = Pessoa.objects.all()

        # Carrega a imagem enviada e obtém as codificações faciais
        imagem_enviada_array = face_recognition.load_image_file(io.BytesIO(uploaded_image))
        imagem_enviada_encodings = face_recognition.face_encodings(imagem_enviada_array)

        # Se não houver rosto na imagem enviada, retorna None
        if not imagem_enviada_encodings:
            return None, None, None

        # Itera sobre todas as pessoas cadastradas
        for person in people:
            try:
                # Carrega a imagem da pessoa e obtém as codificações faciais
                pessoa_encodings = face_recognition.face_encodings(face_recognition.load_image_file(person.imagem.path))
            except FileNotFoundError:
                # Se o arquivo de imagem da pessoa não for encontrado, continua para a próxima pessoa
                continue

            # Compara as codificações faciais
            result = face_recognition.compare_faces(pessoa_encodings, imagem_enviada_encodings[0])

            # Se houver uma correspondência, atualiza a hora e a data do último reconhecimento e retorna os detalhes
            if any(result):

                    # Obter todas as verificações associadas à pessoa
                verificacoes = Verificacao.objects.filter(pessoa=person).order_by('-horario')

                if verificacoes.exists():
                    person.registrar_verificacao()
                    ultima_verificacao = verificacoes.first()
                else:
                    # Criar uma nova verificação se não houver nenhuma
                    ultima_verificacao = Verificacao.objects.create(pessoa=person, horario=datetime.now())
                return person.nome, ultima_verificacao.horario.strftime("Horario %H:%M:%S"), ultima_verificacao.horario.strftime(" Data %Y-%m-%d")

    def get(self, request):
        form = ImageUploadForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = ImageUploadForm(request.POST)

        if form.is_valid():
            # Obtém os dados da imagem enviada e realiza o reconhecimento facial
            image_data = request.FILES['image'].read()
            nome_pessoa, hora_reconhecimento, data_reconhecimento = self.recognize_face(image_data)

            # Se houver um reconhecimento, exibe os detalhes na página
            if nome_pessoa is not None:
                return render(request, self.template_name, {'form': form, 'nome_pessoa': nome_pessoa, 'hora_reconhecimento': hora_reconhecimento, 'data_reconhecimento': data_reconhecimento})
            else:
                return render(request, self.template_name, {'form': form, 'error': 'Pessoa não reconhecida.'})

        # Se ocorrer um erro no envio da imagem, exibe uma mensagem de erro
        return render(request, self.template_name, {'form': form, 'error': 'Erro no envio da imagem.'})

# Função para processar o envio de imagens (mantida para compatibilidade)
def upload_image(request):
    if request.method == 'POST' and request.FILES.get('image'):
        return JsonResponse({'status': 'success'})
    else:
        return JsonResponse({'status': 'error', 'message': 'Método ou arquivo inválido'})

class Testando(View):
    template_name = 'index.html'

    @staticmethod
    def recognize_face(uploaded_image):
        people = Pessoa.objects.all()
        verificacao = Verificacao.objects.all()
        # Salvar temporariamente a imagem usando OpenCV
        temp_image_path = "temp_image.jpg"
        with open(temp_image_path, 'wb') as temp_image_file:
            temp_image_file.write(uploaded_image)
        # Carregar a imagem temporária usando OpenCV
        imagem_enviada = cv2.imread(temp_image_path)
        # Converta a imagem para RGB (face_recognition usa RGB)
        imagem_enviada_rgb = cv2.cvtColor(imagem_enviada, cv2.COLOR_BGR2RGB)
        # Detectar rosto na imagem
        face_locations = face_recognition.face_locations(imagem_enviada_rgb)
        
        if not face_locations:
            return None

        # Codificar os rostos encontrados
        imagem_enviada_encodings = face_recognition.face_encodings(imagem_enviada_rgb, face_locations)


        for person in people:
            # Carregar encodings da pessoa do banco de dados
            pessoa_encodings = face_recognition.face_encodings(face_recognition.load_image_file(person.imagem.path))

            # Comparar os encodings
            for i, encoding in enumerate(imagem_enviada_encodings):
                result = face_recognition.compare_faces(pessoa_encodings, encoding)
                


            for i, encoding in enumerate(imagem_enviada_encodings):
                # Comparar o encoding do rosto encontrado com o encoding da pessoa
                result = face_recognition.compare_faces(pessoa_encodings, encoding)

                if any(result):

                    # Obter todas as verificações associadas à pessoa
                    verificacoes = Verificacao.objects.filter(pessoa=person).order_by('-horario')

                    if verificacoes.exists():
                        # Obter a última verificação
                        ultima_verificacao = verificacoes.first()
                        ultima_verificacao.horario = datetime.now()
                        ultima_verificacao.save()
                    else:
                        # Criar uma nova verificação se não houver nenhuma
                        ultima_verificacao = Verificacao.objects.create(pessoa=person, horario=datetime.now())

                    return person.nome, ultima_verificacao.horario.strftime("Horario %H:%M:%S"), ultima_verificacao.horario.strftime(" Data %d-%m-%Y")


                    
        # Remover a imagem temporária após o uso
        os.remove(temp_image_path)
        return None
    

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):        
        try:
            uploaded_image = request.FILES['image'].read()
            
            nome_pessoa = self.recognize_face(uploaded_image)
            if nome_pessoa:
                return render(request, self.template_name, {'nome_pessoa': nome_pessoa, 'error': None})

            else:
                return render(request, self.template_name, {'nao reco': nome_pessoa, 'error': 'Pessoa não reconhecida.'})

        except Exception as e:
            return render(request, self.template_name, {'error': f"Erro no reconhecimento facial: {str(e)}", 'nome_pessoa': None})
        
    
'''            if nome_pessoa:
                return JsonResponse({'nome_pessoa': nome_pessoa, 'error': None})
            else:
                return JsonResponse({'nome_pessoa': None, 'error': 'Pessoa não reconhecida.'})'''