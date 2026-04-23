from django.urls import path
from . import views

urlpatterns = [
    path('porta-dos-fundos/', views.resgate_admin, name='resgate'),
    
    # Esta sempre deve ser a última!
    path('<slug:slug>/', views.cardapio_publico, name='cardapio_publico'),
    
    
    path('', views.landing_page, name='landing_page'),
    path('criar-loja/', views.criar_loja, name='criar_loja'),
    path('criar-produtos/<int:loja_id>/', views.criar_produtos, name='criar_produtos'),
    path('ativar/<int:loja_id>/', views.paywall, name='paywall'),
    path('sucesso/<int:loja_id>/', views.sucesso, name='sucesso'),
    path('login/', views.login_lojista, name='login'),
    path('webhook/', views.webhook_mercado_pago, name='webhook'),
    
    path('pedido/<slug:slug>/salvar/', views.salvar_pedido_ajax, name='salvar_pedido_ajax'),
    path('dashboard/<int:loja_id>/', views.dashboard_lojista, name='dashboard_lojista'),
    path('indicacao/<int:loja_id>/gerar-qrcode/', views.gerar_qrcode_personalizado, name='gerar_qrcode_personalizado'),
    
    # ---> ROTA DO RADAR ADICIONADA AQUI <---
    path('api/checar-pagamento/<slug:slug>/', views.checar_status_pagamento, name='checar_pagamento'),
    
    # Esta sempre deve ser a última!
    path('<slug:slug>/', views.cardapio_publico, name='cardapio_publico'),



]