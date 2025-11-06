from django.contrib import admin
from django.urls import path
from django.urls import path, include
from django.http import HttpResponse

def home(request):
    return HttpResponse("¡Bienvenido a DuckBank Backend!")

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('loans.urls')),
    path('', home),
]