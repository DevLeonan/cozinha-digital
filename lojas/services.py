import requests
from django.conf import settings

def enviar_whatsapp_recuperacao(numero_do_banco, nome_loja):
    """
    Função para disparar mensagem via API Oficial do WhatsApp Cloud.
    """
    
    # =========================================================
    # 🛑 TRAVA DE SEGURANÇA (MODO TESTE) 🛑
    # Como o Facebook não deixa mandar para clientes reais ainda,
    # vamos FORÇAR o envio para o seu celular cadastrado lá na Meta.
    # Quando for para produção, nós apagamos esta linha abaixo:
    numero_limpo = "5551996799655" # Ex: "5551999999999" (Coloque o seu aqui!)
    # =========================================================

    # 👉 COLOQUE O SEU "ID DO NÚMERO DE TELEFONE" AQUI NA URL (Substitua a palavra):
    url = "https://graph.facebook.com/v17.0/1157401950782092/messages"
    
    headers = {
        "Authorization": "Bearer EAANHZCZBIymboBRWe3S7DtluxRWY8oHap0LKSOIZB84w7i0VMQImab0UZCLLhoAZAnNviL5jEH4iqcAjrPbJ7ngdYtI4116ZBOqqwS7JSOL54db3u7uYxVzCQIZAoB3qpHobm4wIGcGZBTNP88xsJbusuZBsirUslVjn621AWvCjZBDTACeoKXRTahHhQRpRkBzu6egY3PH7pVXdKDi3YbI49jiYoyg3xyUanuhmw3PSYcbIqlf1vZBzelxZBAttIAqEAOVTIIq0mOTZARp91JdAzPY4x8z9A",
        "Content-Type": "application/json"
    }
    
    # Payload padrão Hello World aprovado
    payload = {
        "messaging_product": "whatsapp",
        "to": numero_limpo,
        "type": "template",
        "template": {
            "name": "hello_world",
            "language": { "code": "en_US" }
        }
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            return True
        else:
            print(f"Erro ao enviar: {response.text}")
            return False
    except Exception as e:
        print(f"Falha de conexão: {e}")
        return False