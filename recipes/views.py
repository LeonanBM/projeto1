# views.py
from concurrent.futures import ThreadPoolExecutor
from django.http import HttpResponseForbidden, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.shortcuts import render, redirect
from .models import Pessoa, CadastroEmAnalise, Verificacao, RegistroReconhecimento  # Adicione esta linha
import face_recognition
from django.views.generic import View
from datetime import datetime
from .form import ImageUploadForm
import numpy as np
import pandas as pd
import io
import logging
import cv2
import os
import threading

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


# Função para processar o envio de imagens (mantida para compatibilidade)
def upload_image(request):
    if request.method == 'POST' and request.FILES.get('image'):
        return JsonResponse({'status': 'success'})
    else:
        return JsonResponse({'status': 'error', 'message': 'Método ou arquivo inválido'})


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

class ExportarDadosView(View):
    def get(self, request):
        # Filtrar os registros de reconhecimento por um mês específico (por exemplo, janeiro de 2024)
        registros = RegistroReconhecimento.objects.filter(
            horario__month=1,  # Mês de janeiro
            horario__year=2024  # Ano de 2024
        )

        # Criar um DataFrame do pandas com os dados
        data = {'Pessoa': [registro.pessoa.nome for registro in registros],
                'Horário': [registro.horario.strftime("%d/%m/%Y %H:%M:%S") for registro in registros]}

        df = pd.DataFrame(data)

        # Configurar a resposta HTTP para download do Excel
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename=registros_reconhecimento.xlsx'

        # Salvar o DataFrame no formato Excel
        df.to_excel(response, index=False)

        return response


class ReconhecimentoFacialView(View):
    template_name = 'reconhecimentofacial.html'

    @staticmethod
    def recognize_face(uploaded_image):
        people = Pessoa.objects.only('imagem', 'nome')

        temp_image_path = "temp_image.jpg"
        with open(temp_image_path, 'wb') as temp_image_file:
            temp_image_file.write(uploaded_image)

        imagem_enviada = cv2.imread(temp_image_path)
        imagem_enviada_rgb = cv2.cvtColor(imagem_enviada, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(imagem_enviada_rgb)

        if not face_locations:
            os.remove(temp_image_path)
            return None

        imagem_enviada_encodings = face_recognition.face_encodings(imagem_enviada_rgb, face_locations)

        for person in people:
            try:
                pessoa_encodings = face_recognition.face_encodings(
                    face_recognition.load_image_file(person.imagem.path)
                )[0]

                for encoding in imagem_enviada_encodings:
                    result = face_recognition.compare_faces([pessoa_encodings], encoding)

                    if any(result):
                        verificacoes = Verificacao.objects.filter(pessoa=person).order_by('-horario')

                        if verificacoes.exists():
                            ultima_verificacao = verificacoes.first()
                            ultima_verificacao.horario = datetime.now()
                            ultima_verificacao.save()
                            
                            # Adiciona um registro na tabela RegistroReconhecimento
                            RegistroReconhecimento.objects.create(pessoa=person, horario=datetime.now())

                        else:
                            ultima_verificacao = Verificacao.objects.create(pessoa=person, horario=datetime.now())

                        os.remove(temp_image_path)
                        # Retorna o nome da pessoa e as informações formatadas
                        return person.nome, ultima_verificacao.horario.strftime("%H:%M:%S"), ultima_verificacao.horario.strftime("%d/%m/%Y")

            except FileNotFoundError:
                continue

        os.remove(temp_image_path)
        return None
    
    def get(self, request):
        # Implemente o comportamento desejado para o método GET, se necessário
        return render(request, self.template_name, {'nome_pessoa': None, 'mensagem': None, 'error': None})

    def post(self, request):
        try:
            uploaded_image = request.FILES['image'].read()

            # Chama o método de reconhecimento facial
            nome_pessoa = self.recognize_face(uploaded_image)

            if nome_pessoa:
                mensagem = f'Reconhecimento concluído: {nome_pessoa}'
            else:
                mensagem = 'Nenhuma correspondência encontrada.'

            # Renderiza o template com o resultado
            return render(request, self.template_name, {'nome_pessoa': nome_pessoa, 'mensagem': mensagem, 'error': None})

        except Exception as e:
            # Captura e exibe qualquer exceção que ocorra durante o processamento
            return render(request, self.template_name, {'error': f"Erro no reconhecimento facial: {str(e)}", 'nome_pessoa': None, 'mensagem': None})

class Test(View):
    template_name = 'index.html'

    def get(self, request):
        return render(request, self.template_name)

class Teste(View):
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