from django.db import models
import random
import string

def gerar_senha():
    return ''.join(random.choices(string.digits, k=6))

class Loja(models.Model):
    nome = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, max_length=100, blank=True)
    telefone_whatsapp = models.CharField(max_length=20)
    logo = models.ImageField(upload_to='logos/', blank=True, null=True)
    cor_principal = models.CharField(max_length=20, default='#10b981') # NOVO CAMPO DE COR
    ativo = models.BooleanField(default=False)
    senha_admin = models.CharField(max_length=6, default=gerar_senha) # NOVO CAMPO
    criado_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nome

class Categoria(models.Model):
    loja = models.ForeignKey(Loja, on_delete=models.CASCADE, related_name='categorias')
    nome = models.CharField(max_length=50)

class Produto(models.Model):
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE, related_name='produtos')
    nome = models.CharField(max_length=100)
    descricao = models.TextField(blank=True, null=True)
    preco = models.DecimalField(max_digits=8, decimal_places=2)
    # NOVOS CAMPOS AQUI:
    preco_promocional = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)
    mais_vendido = models.BooleanField(default=False)
    foto = models.ImageField(upload_to='produtos/', blank=True, null=True)

    def __str__(self):
        return self.nome