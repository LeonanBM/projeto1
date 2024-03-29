from .views import *
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include

urlpatterns = [
    path('', Test.as_view(), name='index'),
    path('cadastrar/', CadastrarView.as_view(), name='cadastrar'),
    path('mover-para-pessoas/<int:cadastro_id>/', MovimentarParaPessoaView.as_view(), name='mover-para-pessoas'),
    path('upload/', ReconhecimentoFacialView.as_view(), name='reconhecimentofacial'),
    path('exportar-dados/', ExportarDadosView.as_view(), name='exportar_dados'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)