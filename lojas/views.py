import random
import string
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.text import slugify
from django.views.decorators.clickjacking import xframe_options_exempt
from .models import Loja, Categoria, Produto
import mercadopago
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

# 1. A PÁGINA DE VENDAS (Landing Page)
def landing_page(request):
    return render(request, 'landing.html')

# 2. CONSTRUTOR - PASSO 1: DADOS DA LOJA
def criar_loja(request):
    if request.method == 'POST':
        nome = request.POST.get('nome')
        whatsapp = request.POST.get('whatsapp')
        logo = request.FILES.get('logo')
        cor = request.POST.get('cor_principal')

        # Cria o link base limpo
        slug_base = slugify(nome)
        # Gera 4 letras/números aleatórios para garantir que a URL nunca repita
        sufixo = ''.join(random.choices(string.ascii_lowercase + string.digits, k=4))
        slug_unico = f"{slug_base}-{sufixo}"

        # Cria a loja bloqueada com o link único garantido
        loja = Loja.objects.create(
            nome=nome,
            telefone_whatsapp=whatsapp,
            logo=logo,
            cor_principal=cor,
            slug=slug_unico 
        )
        # Já cria uma categoria padrão para facilitar
        Categoria.objects.create(loja=loja, nome="Cardápio")
        
        return redirect('criar_produtos', loja_id=loja.id)
    
    return render(request, 'criar_loja.html')

# 3. CONSTRUTOR - PASSO 2: ADICIONAR PRODUTOS E CATEGORIAS
def criar_produtos(request, loja_id):
    loja = get_object_or_404(Loja, id=loja_id)
    categorias = loja.categorias.all()

    if request.method == 'POST':
        acao = request.POST.get('acao')
        
        # Se ele clicou em "Criar Categoria"
        if acao == 'nova_categoria':
            nome_cat = request.POST.get('nome_categoria')
            if nome_cat:
                Categoria.objects.create(loja=loja, nome=nome_cat)
                
        # Se ele clicou em "Salvar Produto"
        elif acao == 'novo_produto':
            cat_id = request.POST.get('categoria_id')
            categoria = get_object_or_404(Categoria, id=cat_id)
            nome = request.POST.get('nome')
            preco = request.POST.get('preco')
            preco_promo = request.POST.get('preco_promocional')
            mais_vendido = request.POST.get('mais_vendido') == 'on'
            foto = request.FILES.get('foto')
            
            # Converte o preço promo para salvar direitinho, ou deixa vazio
            preco_promo_val = preco_promo if preco_promo else None
            
            Produto.objects.create(
                categoria=categoria, 
                nome=nome, 
                preco=preco, 
                preco_promocional=preco_promo_val,
                mais_vendido=mais_vendido,
                foto=foto
            )
        return redirect('criar_produtos', loja_id=loja.id)

    return render(request, 'criar_produtos.html', {'loja': loja, 'categorias': categorias})

# Configure suas credenciais do Mercado Pago
sdk = mercadopago.SDK("APP_USR-5402725203039388-020123-10a75c260cf12f6663994256fc156b5d-1365742803")

# 4. A BARREIRA DE PAGAMENTO (AGORA COM PIX REAL)
def paywall(request, loja_id):
    loja = get_object_or_404(Loja, id=loja_id)
    
    # Se ele já pagou e atualizar a página, manda direto pro Sucesso
    if loja.ativo:
        return redirect('sucesso', loja_id=loja.id)

    pix_data = None
    
    # Gera um código PIX novo toda vez que a página carrega
    payment_data = {
        "transaction_amount": 19.99,
        "description": f"Ativação do Cardápio - {loja.nome}",
        "payment_method_id": "pix",
        "payer": {
            "email": "cliente@cozinhadigital.com",
            "first_name": loja.nome,
        },
        "external_reference": str(loja.id) # Carimba a transação com o ID da loja
    }
    
    result = sdk.payment().create(payment_data)
    payment = result["response"]
    
    if "point_of_interaction" in payment:
        pix_data = {
            "qr_code": payment["point_of_interaction"]["transaction_data"]["qr_code"],
            "qr_code_base64": payment["point_of_interaction"]["transaction_data"]["qr_code_base64"],
        }

    return render(request, 'paywall.html', {'loja': loja, 'pix': pix_data})

# ANTENA DO MERCADO PAGO (WEBHOOK AUTOMÁTICO)
@csrf_exempt
def webhook_mercado_pago(request):
    if request.method == "POST":
        data = request.GET
        if "data.id" in data:
            payment_id = data.get("data.id")
            payment_info = sdk.payment().get(payment_id)["response"]
            
            if payment_info.get("status") == "approved":
                loja_id = payment_info.get("external_reference")
                loja = Loja.objects.filter(id=loja_id).first()
                if loja and not loja.ativo:
                    loja.ativo = True
                    loja.save()
                    
    return JsonResponse({"status": "sucesso"})
    
# 6. TELA DE SUCESSO E ENTREGA DAS CHAVES
def sucesso(request, loja_id):
    loja = get_object_or_404(Loja, id=loja_id)
    return render(request, 'sucesso.html', {'loja': loja})

# 7. O SISTEMA DE LOGIN DO LOJISTA
def login_lojista(request):
    if request.method == 'POST':
        whatsapp = request.POST.get('whatsapp')
        senha = request.POST.get('senha')
        
        try:
            loja = Loja.objects.get(telefone_whatsapp=whatsapp, senha_admin=senha)
            return redirect('criar_produtos', loja_id=loja.id)
        except Loja.DoesNotExist:
            return render(request, 'login.html', {'erro': 'WhatsApp ou Senha incorretos!'})
            
    return render(request, 'login.html')

# 5. O CARDÁPIO FINAL DO CLIENTE
@xframe_options_exempt  # <-- ISSO AQUI LIBERA A PRÉVIA NO CELULAR!
def cardapio_publico(request, slug):
    loja = get_object_or_404(Loja, slug=slug)
    categorias = loja.categorias.all()
    produtos = Produto.objects.filter(categoria__loja=loja)
    
    is_preview = not loja.ativo 

    return render(request, 'cardapio.html', {
        'loja': loja, 
        'categorias': categorias, 
        'produtos': produtos,
        'is_preview': is_preview
    })