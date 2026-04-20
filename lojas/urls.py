from django.urls import path
from . import views

urlpatterns = [
    path('', views.landing_page, name='landing_page'),
    path('criar-loja/', views.criar_loja, name='criar_loja'),
    path('criar-produtos/<int:loja_id>/', views.criar_produtos, name='criar_produtos'),
    path('ativar/<int:loja_id>/', views.paywall, name='paywall'),
    
    # NOVAS ROTAS AQUI:
    path('sucesso/<int:loja_id>/', views.sucesso, name='sucesso'),
    path('login/', views.login_lojista, name='login'),
    
    path('<slug:slug>/', views.cardapio_publico, name='cardapio_publico'),
    path('ativar/<int:loja_id>/', views.paywall, name='paywall'),
    path('sucesso/<int:loja_id>/', views.sucesso, name='sucesso'),
    path('webhook/', views.webhook_mercado_pago, name='webhook'), # <-- ROTA NOVA
]