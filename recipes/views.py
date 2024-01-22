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
            return melhores_resultados[0][0], Test.get_current_datetime()

        except Exception as e:
            return None, f"Erro no reconhecimento facial: {str(e)}"

    @staticmethod
    def get_current_datetime():
        from datetime import datetime
        # Adicionando uma quebra de linha (\n) entre a data e a hora
        return datetime.now().strftime("%d-%m-%Y\n%H:%M:%S")

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        try:
            # Certifique-se de que 'image' está presente nos arquivos da solicitação
            if 'image' not in request.FILES:
                return render(request, self.template_name, {'error': 'Nenhuma imagem enviada.'})

            uploaded_image = request.FILES['image'].read()

            # Chame recognize_face para obter o nome da pessoa e a data/hora do reconhecimento
            nome_pessoa, data_hora_reconhecimento = self.recognize_face(uploaded_image)

            if nome_pessoa:
                # Separar a data e a hora aqui
                data_reconhecimento, hora_reconhecimento = data_hora_reconhecimento.split("\n")

                return render(request, self.template_name, {
                    'nome_pessoa': nome_pessoa,
                    'data_reconhecimento': data_reconhecimento,
                    'hora_reconhecimento': hora_reconhecimento
                })
            else:
                return render(request, self.template_name, {'error': 'Pessoa não reconhecida.'})

        except Exception as e:
            return render(request, self.template_name, {'error': f"Erro no reconhecimento facial: {str(e)}"})
