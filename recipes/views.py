# views.py
from django.shortcuts import render
from .models import Pessoa
import face_recognition
from django.views.generic import View
import numpy as np
import io

class Test(View):
    template_name = 'index.html'

    @staticmethod
    def recognize_face(uploaded_image):
        try:
            # Carregar a imagem enviada
            imagem_enviada_array = face_recognition.load_image_file(io.BytesIO(uploaded_image))
            imagem_enviada_encodings = face_recognition.face_encodings(imagem_enviada_array)

            if not imagem_enviada_encodings:
                return None, 'Nenhum rosto encontrado na imagem.'

            # Obter encodings de todas as pessoas do banco de dados
            pessoas = Pessoa.objects.all()
            melhores_resultados = []

            for pessoa in pessoas:
                # Carregar encodings da pessoa do banco de dados
                pessoa_encodings = face_recognition.face_encodings(face_recognition.load_image_file(pessoa.imagem.path))

                # Comparar os encodings
                resultados = face_recognition.compare_faces(pessoa_encodings, imagem_enviada_encodings[0])
                
                # Calcular a média da distância dos resultados (quanto menor, mais similar)
                distancia_media = np.mean(face_recognition.face_distance(pessoa_encodings, imagem_enviada_encodings[0]))

                melhores_resultados.append((pessoa.nome, distancia_media))

            # Ordenar os resultados com base na distância (quanto menor, mais similar)
            melhores_resultados.sort(key=lambda x: x[1])

            # Retornar o nome da pessoa mais similar
            return melhores_resultados[0][0], None

        except Exception as e:
            return None, f"Erro no reconhecimento facial: {str(e)}"

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        try:
            # Certifique-se de que 'image' está presente nos arquivos da solicitação
            if 'image' not in request.FILES:
                return render(request, self.template_name, {'error': 'Nenhuma imagem enviada.'})

            uploaded_image = request.FILES['image'].read()
            
            # Reconhecer o rosto na imagem
            nome_pessoa, erro = self.recognize_face(uploaded_image)

            if nome_pessoa:
                return render(request, self.template_name, {'nome_pessoa': nome_pessoa})
            else:
                return render(request, self.template_name, {'error': erro})

        except Exception as e:
            return render(request, self.template_name, {'error': f"Erro no reconhecimento facial: {str(e)}"})
