from .views import *
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include

urlpatterns = [
    path('', Test.as_view(), name='index'),
    path('cadastrar/', CadastrarView.as_view(), name='cadastrar'),
    path('reconhecimentofacial/', ReconhecimentoFacialView.as_view(), name='reconhecimentofacial'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)