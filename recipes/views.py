# views.py
from concurrent.futures import ThreadPoolExecutor
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect
from django.shortcuts import render, redirect
from .models import Pessoa, CadastroEmAnalise
import face_recognition
from django.views.generic import View
import numpy as np
import io
import logging

logger = logging.getLogger(__name__)

class MovimentarParaPessoaView(View):
    def post(self, request, cadastro_id):
        try:
            # Obter o cadastro em análise pelo ID
            cadastro_analise = get_object_or_404(CadastroEmAnalise, pk=cadastro_id)

            # Adicionar lógica para mover para a tabela de pessoas
            pessoa = Pessoa.objects.create(
                nome=cadastro_analise.nome,
                imagem=cadastro_analise.imagem,
                encodings=cadastro_analise.encodings
            )

            # Marcar a análise como concluída
            cadastro_analise.analise_concluida = True
            cadastro_analise.save()

            logger.info(f"Cadastro movido para pessoas: {pessoa.nome}")

            # Redirecionar para a página correta após a movimentação
            return redirect('admin:recipes_cadastroemanalise_changelist')

        except Exception as e:
            logger.error(f"Erro na movimentação para pessoas: {str(e)}")
            # Adicione um retorno ou redirecionamento adequado em caso de erro
            return redirect('admin:recipes_cadastroemanalise_changelist')

    def get(self, request, cadastro_id):
        try:
            # Obter o cadastro em análise pelo ID
            cadastro_analise = get_object_or_404(CadastroEmAnalise, pk=cadastro_id)

            # Renderizar a página de confirmação para solicitações GET
            return render(
                request,
                'movimentar_para_pessoa_confirmacao.html',
                {'cadastro_analise': cadastro_analise}
            )

        except Exception as e:
            logger.error(f"Erro ao exibir página de confirmação: {str(e)}")
            # Adicione um retorno ou redirecionamento adequado em caso de erro
            return HttpResponseForbidden("Erro ao processar a solicitação.")

class CadastrarView(View):
    template_name = 'cadastrar.html'

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        try:
            # Processar os dados do formulário
            nome = request.POST.get('nome')
            foto = request.FILES.get('foto')

            # Verificar se uma imagem foi realmente enviada
            if foto is None:
                mensagem = 'Nenhuma imagem enviada. Por favor, escolha uma imagem.'
            else:
                try:
                    # Verificar se há um rosto na foto
                    foto_array = face_recognition.load_image_file(io.BytesIO(foto.read()))
                    face_locations = face_recognition.face_locations(foto_array)

                    if not face_locations:
                        # Rosto não detectado
                        mensagem = 'Rosto não detectado, tente novamente.'
                    else:
                        # Também salvar dados na tabela CadastroEmAnalise
                        CadastroEmAnalise.objects.create(nome=nome, imagem=foto)

                        # Rosto detectado, aqui você pode adicionar a lógica para salvar os dados no banco de dados, se necessário
                        mensagem = 'Dados enviados com sucesso.'

                except Exception as e:
                    # Tratar erros, se houver algum problema com a detecção facial
                    mensagem = f"Erro na detecção facial: {str(e)}"

            # Adicione logs para depuração
            logger.info(f"Nome: {nome}, Mensagem: {mensagem}")

            # Atualizar o contexto
            context = {'nome': nome, 'mensagem': mensagem}

            return render(request, self.template_name, context)

        except Exception as e:
            # Adicione logs para capturar erros gerais
            logger.error(f"Erro no processamento do formulário: {str(e)}")
            # Configurando mensagem como None para não exibi-la no template
            mensagem = None
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

            for pessoa in pessoas:
                # Carregar encodings da pessoa do banco de dados
                pessoa_encodings = face_recognition.face_encodings(face_recognition.load_image_file(pessoa.imagem.path))

                # Comparar os encodings
                resultados = face_recognition.compare_faces(pessoa_encodings, imagem_enviada_encodings[0], tolerance=0.6)
                
                # Calcular a média da distância dos resultados (quanto menor, mais similar)
                distancia_media = np.mean(face_recognition.face_distance(pessoa_encodings, imagem_enviada_encodings[0]))

                if any(resultados) and distancia_media < 0.6:
                    # Se houver correspondência com confiança suficientemente alta (98%)
                    resultados_encontrados.append((pessoa.nome, distancia_media))

            # Ordenar os resultados com base na distância (quanto menor, mais similar)
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
