import random
import string
import uuid
from django.db import models
from django.utils.text import slugify

def gerar_senha():
    return ''.join(random.choices(string.digits, k=6))

class Loja(models.Model):
    nome = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, max_length=100, blank=True)
    telefone_whatsapp = models.CharField(max_length=20)
    logo = models.ImageField(upload_to='logos/', blank=True, null=True)
    cor_principal = models.CharField(max_length=20, default='#10b981')
    ativo = models.BooleanField(default=False)
    senha_admin = models.CharField(max_length=6, default=gerar_senha)
    criado_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nome
        
        
class Categoria(models.Model):
    loja = models.ForeignKey(Loja, on_delete=models.CASCADE, related_name='categorias')
    nome = models.CharField(max_length=50)

    def __str__(self):
        return self.nome

class Produto(models.Model):
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE, related_name='produtos')
    nome = models.CharField(max_length=100)
    descricao = models.TextField(blank=True, null=True)
    preco = models.DecimalField(max_digits=8, decimal_places=2)
    preco_promocional = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)
    mais_vendido = models.BooleanField(default=False)
    foto = models.ImageField(upload_to='produtos/', blank=True, null=True)

    def __str__(self):
        return self.nome

class Pedido(models.Model):
    loja = models.ForeignKey(Loja, on_delete=models.CASCADE, related_name='pedidos')
    nome_cliente = models.CharField(max_length=100)
    endereco_entrega = models.TextField()
    forma_pagamento = models.CharField(max_length=50)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-criado_em']

    def __str__(self):
        return f"Pedido {self.id} - {self.nome_cliente}"

class ItemPedido(models.Model):
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name='itens')
    produto_nome = models.CharField(max_length=100)
    produto_preco = models.DecimalField(max_digits=8, decimal_places=2)

class Indicacao(models.Model):
    lojista_indicador = models.ForeignKey(Loja, on_delete=models.CASCADE, related_name='indicacoes_geradas')
    loja_indicada = models.OneToOneField(Loja, on_delete=models.SET_NULL, null=True, blank=True, related_name='origem_indicacao')
    codigo_indicacao = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    status = models.CharField(max_length=20, default='pendente') # pendente, pago, recompensa_entregue
    criado_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Indicação de {self.lojista_indicador.nome}"
        
