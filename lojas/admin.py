from django.contrib import admin
from .models import Loja, Categoria, Produto

admin.site.register(Loja)
admin.site.register(Categoria)
admin.site.register(Produto)