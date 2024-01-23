# views.py
from concurrent.futures import ThreadPoolExecutor
from django.shortcuts import render
from .models import Pessoa
import face_recognition
from django.views.generic import View
import numpy as np
import io

class CadastrarView(View):
    template_name = 'cadastrar.html'

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        # Processar os dados do formulário
        nome = request.POST.get('nome')
        foto = request.FILES.get('foto')

        try:
            # Verificar se há um rosto na foto
            foto_array = face_recognition.load_image_file(io.BytesIO(foto.read()))
            face_locations = face_recognition.face_locations(foto_array)

            if not face_locations:
                # Rosto não detectado
                mensagem = 'Rosto não detectado, tente novamente.'
            else:
                # Rosto detectado, aqui você pode adicionar a lógica para salvar os dados no banco de dados, se necessário
                mensagem = 'Dados enviados com sucesso.'

        except Exception as e:
            # Tratar erros, se houver algum problema com a detecção facial
            mensagem = f"Erro na detecção facial: {str(e)}"

        # Atualizar o contexto
        context = {'nome': nome, 'mensagem': mensagem}

        return render(request, self.template_name, context)

class ReconhecimentoFacialView(View):
    template_name = 'reconhecimentofacial.html'

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

            if nome_pessoa is not None:
                # Separar a data e a hora aqui
                data_reconhecimento, hora_reconhecimento = data_hora_reconhecimento.split("\n")

                return render(request, self.template_name, {
                    'nome_pessoa': nome_pessoa,
                    'data_reconhecimento': data_reconhecimento,
                    'hora_reconhecimento': hora_reconhecimento
                })
            else:
                # Se não for possível reconhecer o rosto
                return render(request, self.template_name, {'error': 'Erro no reconhecimento facial. Tente novamente ou realize o cadastro.'})

        except Exception as e:
            # Se ocorrer um erro geral durante o processamento
            return render(request, self.template_name, {'error': f"Erro: {str(e)}"})

    @staticmethod
    def recognize_face(uploaded_image):
        try:
            # Carregar a imagem enviada
            imagem_enviada_array = face_recognition.load_image_file(io.BytesIO(uploaded_image))
            imagem_enviada_encodings = face_recognition.face_encodings(imagem_enviada_array)

            if not imagem_enviada_encodings:
                return None, 'Rosto não detectado, tire uma nova foto.'

            # Obter encodings de todas as pessoas do banco de dados
            pessoas = Pessoa.objects.all()
            resultados_encontrados = []

            def comparar_encodings(pessoa):
                pessoa_encodings = face_recognition.face_encodings(face_recognition.load_image_file(pessoa.imagem.path))
                resultados = face_recognition.compare_faces(pessoa_encodings, imagem_enviada_encodings[0], tolerance=0.6)
                distancia_media = np.mean(face_recognition.face_distance(pessoa_encodings, imagem_enviada_encodings[0]))

                if any(resultados) and distancia_media < 0.6:
                    resultados_encontrados.append((pessoa.nome, distancia_media))

            # Use ThreadPoolExecutor para paralelizar o processamento
            with ThreadPoolExecutor() as executor:
                executor.map(comparar_encodings, pessoas)

            resultados_encontrados.sort(key=lambda x: x[1])

            if resultados_encontrados:
                # Retornar o nome da pessoa mais similar
                return resultados_encontrados[0][0], ReconhecimentoFacialView.get_current_datetime()
            else:
                # Rosto detectado, mas não reconhecido
                return None, 'Rosto detectado, mas não reconhecido. Realize o cadastro.'

        except Exception as e:
            return None, f"Erro no reconhecimento facial: {str(e)}"
    @staticmethod
    def get_current_datetime():
        from datetime import datetime
        # Adicionando uma quebra de linha (\n) entre a data e a hora
        return datetime.now().strftime("%d-%m-%Y\n%H:%M:%S")


class Test(View):
    template_name = 'index.html'

    def get(self, request):
        return render(request, self.template_name)
