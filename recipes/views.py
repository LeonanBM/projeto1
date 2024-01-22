# views.py
from django.shortcuts import render
from .models import Pessoa
import face_recognition
from django.http import HttpResponse
import numpy as np
from django.views.generic import TemplateView,CreateView,View,ListView,UpdateView,DeleteView
import io

class Test(View):
    template_name = 'index.html'

    @staticmethod
    def recognize_face(uploaded_image):
        people = Pessoa.objects.all()

        # Criar um objeto de bytes a partir do conteúdo da imagem
        imagem_enviada_array = face_recognition.load_image_file(io.BytesIO(uploaded_image))
        imagem_enviada_encodings = face_recognition.face_encodings(imagem_enviada_array)

        if not imagem_enviada_encodings:
            return None

        for person in people:
            # Carregar encodings da pessoa do banco de dados
            pessoa_encodings = face_recognition.face_encodings(face_recognition.load_image_file(person.imagem.path))

            # Comparar os encodings
            result = face_recognition.compare_faces(pessoa_encodings, imagem_enviada_encodings[0])

            if any(result):
                return person.nome  # Corrigido para person.nome

        return None

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        try:
            uploaded_image = request.FILES['image'].read()
            
            nome_pessoa = self.recognize_face(uploaded_image)

            if nome_pessoa:
                return render(request, self.template_name, {'nome_pessoa': nome_pessoa})
            else:
                return render(request, self.template_name, {'error': 'Pessoa não reconhecida.'})

        except Exception as e:
            return render(request, self.template_name, {'error': f"Erro no reconhecimento facial: {str(e)}"})
