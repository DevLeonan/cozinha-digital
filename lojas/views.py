import random
import string
import uuid
import json
import mercadopago
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.text import slugify
from django.views.decorators.clickjacking import xframe_options_exempt
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Count, Sum
from .models import Loja, Categoria, Produto, Pedido, ItemPedido, Indicacao
from django.http import HttpResponse
from django.contrib.auth.models import User # Coloque isso lá no topo junto com os outros imports!

# ... seus outros códigos ...

def resgate_admin(request):
    """ Função secreta para recuperar o acesso ao painel """
    # Se o usuário 'leoadmin' não existir, ele cria
    if not User.objects.filter(username='leoadmin').exists():
        User.objects.create_superuser('leoadmin', '', 'senha12345')
        return HttpResponse("<h1>Painel Hackeado com Sucesso! 🚀</h1> <p>Usuário: <b>leoadmin</b> <br> Senha: <b>senha12345</b></p> <a href='/admin/'>Clique aqui para fazer login</a>")
    else:
        # Se ele já existir de alguma tentativa antiga, força a trocar a senha
        user = User.objects.get(username='leoadmin')
        user.set_password('senha12345')
        user.save()
        return HttpResponse("<h1>Senha resetada com sucesso! 🚀</h1> <p>Usuário: <b>leoadmin</b> <br> Senha: <b>senha12345</b></p> <a href='/admin/'>Clique aqui para fazer login</a>")
        
       
# Configure suas credenciais do Mercado Pago
sdk = mercadopago.SDK("APP_USR-5402725203039388-020123-10a75c260cf12f6663994256fc156b5d-1365742803")

def landing_page(request):
    return render(request, 'landing.html')

def criar_loja(request):
    if request.method == 'POST':
        nome = request.POST.get('nome')
        whatsapp = request.POST.get('whatsapp')
        logo = request.FILES.get('logo')
        cor = request.POST.get('cor_principal')

        slug_base = slugify(nome)
        sufixo = ''.join(random.choices(string.ascii_lowercase + string.digits, k=4))
        slug_unico = f"{slug_base}-{sufixo}"

        ref_uuid_str = request.GET.get('ref')
        indicacao_pendente = None
        if ref_uuid_str:
            try:
                ref_uuid = uuid.UUID(ref_uuid_str)
                indicacao_pendente = Indicacao.objects.get(codigo_indicacao=ref_uuid, status='pendente')
            except (ValueError, Indicacao.DoesNotExist):
                pass

        loja = Loja.objects.create(
            nome=nome,
            telefone_whatsapp=whatsapp,
            logo=logo,
            cor_principal=cor,
            slug=slug_unico 
        )
        Categoria.objects.create(loja=loja, nome="Cardápio")
        
        if indicacao_pendente:
            indicacao_pendente.loja_indicada = loja
            indicacao_pendente.save()

        return redirect('criar_produtos', loja_id=loja.id)
    
    return render(request, 'criar_loja.html')

def criar_produtos(request, loja_id):
    loja = get_object_or_404(Loja, id=loja_id)
    categorias = loja.categorias.all()

    indicacao, created = Indicacao.objects.get_or_create(lojista_indicador=loja)

    if request.method == 'POST':
        acao = request.POST.get('acao')
        if acao == 'nova_categoria':
            nome_cat = request.POST.get('nome_categoria')
            if nome_cat:
                Categoria.objects.create(loja=loja, nome=nome_cat)
                
        elif acao == 'novo_produto':
            cat_id = request.POST.get('categoria_id')
            categoria = get_object_or_404(Categoria, id=cat_id)
            nome = request.POST.get('nome')
            preco = request.POST.get('preco')
            preco_promo = request.POST.get('preco_promocional')
            mais_vendido = request.POST.get('mais_vendido') == 'on'
            foto = request.FILES.get('foto')
            
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

    return render(request, 'criar_produtos.html', {
        'loja': loja, 
        'categorias': categorias,
        'indicacao_uuid': indicacao.codigo_indicacao
    })

def paywall(request, loja_id):
    loja = get_object_or_404(Loja, id=loja_id)
    
    if loja.ativo:
        return redirect('sucesso', loja_id=loja.id)

    pix_data = None
    payment_data = {
        "transaction_amount": 19.99,
        "description": f"Ativação do Cardápio - {loja.nome}",
        "payment_method_id": "pix",
        "payer": {"email": "cliente@cozinhadigital.com", "first_name": loja.nome},
        "external_reference": str(loja.id)
    }
    
    result = sdk.payment().create(payment_data)
    payment = result.get("response", {})
    
    if "point_of_interaction" in payment:
        pix_data = {
            "qr_code": payment["point_of_interaction"]["transaction_data"]["qr_code"],
            "qr_code_base64": payment["point_of_interaction"]["transaction_data"]["qr_code_base64"],
        }

    return render(request, 'paywall.html', {'loja': loja, 'pix': pix_data})

@csrf_exempt
def webhook_mercado_pago(request):
    if request.method == "POST":
        data = request.GET
        if "data.id" in data:
            payment_id = data.get("data.id")
            payment_info = sdk.payment().get(payment_id).get("response", {})
            
            if payment_info.get("status") == "approved":
                loja_id = payment_info.get("external_reference")
                loja = Loja.objects.filter(id=loja_id).first()
                if loja and not loja.ativo:
                    loja.ativo = True
                    loja.save()
                    
                    indicacao_paga = Indicacao.objects.filter(loja_indicada=loja, status='pendente').first()
                    if indicacao_paga:
                        indicacao_paga.status = 'pago'
                        indicacao_paga.save()
                        
    return JsonResponse({"status": "sucesso"})

def sucesso(request, loja_id):
    loja = get_object_or_404(Loja, id=loja_id)
    return render(request, 'sucesso.html', {'loja': loja})

def login_lojista(request):
    if request.method == 'POST':
        whatsapp = request.POST.get('whatsapp')
        senha = request.POST.get('senha')
        try:
            loja = Loja.objects.get(telefone_whatsapp=whatsapp, senha_admin=senha)
            return redirect('dashboard_lojista', loja_id=loja.id)
        except Loja.DoesNotExist:
            return render(request, 'login.html', {'erro': 'WhatsApp ou Senha incorretos!'})
    return render(request, 'login.html')

def salvar_pedido_ajax(request, slug):
    if request.method == 'POST':
        loja = get_object_or_404(Loja, slug=slug)
        data = json.loads(request.body)
        
        carrinho = data.get('carrinho', [])
        total = data.get('total')
        nome_cliente = data.get('nomeCliente')
        endereco_cliente = data.get('enderecoCliente')
        pagamento_cliente = data.get('pagamentoCliente')

        if not carrinho or not nome_cliente or not endereco_cliente or not pagamento_cliente:
             return JsonResponse({'status': 'erro', 'mensagem': 'Dados incompletos'}, status=400)

        pedido = Pedido.objects.create(
            loja=loja, nome_cliente=nome_cliente,
            endereco_entrega=endereco_cliente, forma_pagamento=pagamento_cliente, total=total
        )
        
        for item in carrinho:
            ItemPedido.objects.create(pedido=pedido, produto_nome=item['nome'], produto_preco=item['preco'])
            
        return JsonResponse({'status': 'sucesso', 'pedido_id': pedido.id})
    return JsonResponse({'status': 'erro'}, status=405)

def dashboard_lojista(request, loja_id):
    loja = get_object_or_404(Loja, id=loja_id)
    total_pedidos = loja.pedidos.count()
    faturamento_total = loja.pedidos.aggregate(Sum('total'))['total__sum'] or 0
    faturamento_pix = loja.pedidos.filter(forma_pagamento='PIX').aggregate(Sum('total'))['total__sum'] or 0
    
    produtos_ranking = ItemPedido.objects.filter(pedido__loja=loja) \
                                        .values('produto_nome') \
                                        .annotate(total_vendas=Count('id')) \
                                        .order_by('-total_vendas')[:5]
    pedidos_recentes = loja.pedidos.prefetch_related('itens').all()[:20]

    return render(request, 'dashboard.html', {
        'loja': loja, 'total_pedidos': total_pedidos, 'faturamento_total': faturamento_total,
        'faturamento_pix': faturamento_pix, 'produtos_ranking': produtos_ranking, 'pedidos_recentes': pedidos_recentes
    })

def checar_status_pagamento(request, slug):
    try:
        loja = Loja.objects.get(slug=slug)
        
        # Se a loja já está ativa (pagou)
        if loja.ativo == True: 
            return JsonResponse({
                'aprovado': True,
                # A MÁGICA ACONTECE AQUI: Usando o nome exato e o ID da loja!
                'url_redirecionamento': reverse('sucesso', args=[loja.id]) 
            })
        else:
            return JsonResponse({'aprovado': False})
            
    except Loja.DoesNotExist:
        return JsonResponse({'aprovado': False, 'erro': 'Loja não encontrada'})

@xframe_options_exempt
def gerar_qrcode_personalizado(request, loja_id):
    loja = get_object_or_404(Loja, id=loja_id)
    indicacao_paga = Indicacao.objects.filter(lojista_indicador=loja, status='pago').first()
    
    if indicacao_paga:
        indicacao_paga.status = 'recompensa_entregue'
        indicacao_paga.save()
        return redirect('sucesso', loja_id=loja.id)

    return redirect('criar_produtos', loja_id=loja.id)

@xframe_options_exempt
def cardapio_publico(request, slug):
    loja = get_object_or_404(Loja, slug=slug)
    categorias = loja.categorias.all()
    produtos = Produto.objects.filter(categoria__loja=loja)
    is_preview = not loja.ativo 

    return render(request, 'cardapio.html', {
        'loja': loja, 'categorias': categorias, 'produtos': produtos, 'is_preview': is_preview
    })