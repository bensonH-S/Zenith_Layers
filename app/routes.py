# Importa o Blueprint para organizar as rotas da aplicação de forma modular
from flask import Blueprint, request, jsonify, render_template, redirect, url_for, Response
# Importa bibliotecas para fazer requisições à API do DeepSeek e carregar variáveis do .env
import requests
import os
# Importa o Client da Twilio para enviar mensagens
from twilio.rest import Client
# Importa funções e classes do Flask-Login para gerenciar autenticação
from flask_login import login_required, current_user, login_user, logout_user
# Importa funções do models.py para manipulação de dados
from app.models import Usuario, registrar_usuario, login_usuario, login_usuario_web, cadastrar_usuario_empresa, get_persona_by_empresa, save_persona, get_empresa_id_by_usuario
from database.connection import connect_db
import logging

# Configura logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Cria um blueprint chamado 'main' para agrupar as rotas da aplicação
main = Blueprint('main', __name__)

# Função para chamar a API do DeepSeek-V3
def call_deepseek_api(message):
    """Chama a API do DeepSeek-V3 para processar uma mensagem.

    Args:
        message (str): Mensagem a ser processada pela API.

    Returns:
        str: Resposta da API ou mensagem de erro.
    """
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        return "Erro: Chave de API do DeepSeek não encontrada no .env"
    endpoint = "https://api.deepseek.com/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": "Você é um assistente prestativo."},
            {"role": "user", "content": message}
        ],
        "max_tokens": 150,
        "temperature": 0.7,
        "stream": False
    }
    response = requests.post(endpoint, json=payload, headers=headers)
    if response.status_code == 200:
        return response.json().get('choices')[0].get('message').get('content')
    else:
        return f"Erro na API: {response.status_code} - {response.json()}"

# Rota para registrar um usuário via API (recebe dados em formato JSON)
@main.route('/registro', methods=['POST'])
def registrar_usuario_route():
    """Registra um novo usuário via API.

    Recebe dados em JSON (nome, email, senha) e registra o usuário no banco de dados.

    Returns:
        JSON: Mensagem de sucesso ou erro.
    """
    data = request.json
    nome = data.get('nome')
    email = data.get('email')
    senha = data.get('senha')

    # Valida se todos os campos obrigatórios foram preenchidos
    if not all([nome, email, senha]):
        return jsonify({'erro': 'Todos os campos são obrigatórios'}), 400

    # Chama a função do modelo para registrar o usuário
    sucesso = registrar_usuario(nome, email, senha)
    if sucesso:
        return jsonify({'mensagem': 'Usuário registrado com sucesso!'}), 201
    else:
        return jsonify({'erro': 'Erro ao registrar usuário'}), 500

# Rota para login de usuário via API (recebe dados em formato JSON)
@main.route('/login', methods=['POST'])
def login_usuario_route():
    """Autentica um usuário via API.

    Recebe email e senha em JSON, verifica as credenciais e retorna mensagem de sucesso ou erro.

    Returns:
        JSON: Mensagem de sucesso ou erro.
    """
    data = request.json
    email = data.get('email')
    senha = data.get('senha')

    # Valida se os campos obrigatórios foram preenchidos
    if not all([email, senha]):
        return jsonify({'erro': 'Email e senha são obrigatórios'}), 400

    # Chama a função do modelo para autenticar o usuário
    usuario = login_usuario(email, senha)
    if not usuario:
        return jsonify({'erro': 'Usuário não encontrado ou senha incorreta'}), 401

    return jsonify({'mensagem': f"Bem-vindo, {usuario['nome']}!"}), 200

# Rota para exibir a página de login (método GET)
@main.route('/login', methods=['GET'])
def login_page():
    """Exibe a página de login.

    Returns:
        HTML: Template login.html renderizado.
    """
    return render_template('login.html')

# Rota para login via formulário web (método POST)
@main.route('/login-web', methods=['POST'])
def login_web():
    """Autentica um usuário via formulário web e redireciona para o painel.

    Recebe email e senha do formulário, autentica o usuário e inicia a sessão.

    Returns:
        Redireciona para o painel ou retorna mensagem de erro.
    """
    email = request.form.get('email')
    senha = request.form.get('senha')

    # Chama a função do modelo para autenticar o usuário
    user_obj = login_usuario_web(email, senha)
    if user_obj:
        login_user(user_obj)
        return redirect(url_for('main.painel'))

    return "E-mail ou senha incorretos."

# Rota para página de cadastro (métodos GET e POST)
@main.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    """Gerencia o cadastro de usuários e empresas.

    - GET: Exibe o formulário de cadastro.
    - POST: Processa o formulário e cadastra o usuário e a empresa.

    Returns:
        HTML ou mensagem: Template cadastro.html (GET) ou mensagem de sucesso/erro (POST).
    """
    if request.method == 'POST':
        # Dados do usuário extraídos do formulário
        dados_usuario = {
            'nome': request.form['nome'],
            'email': request.form['email'],
            'senha': request.form['senha'],
            'cpf': request.form['cpf'],
            'data_nascimento': request.form['data_nascimento'],
            'cep': request.form['cep'],
            'endereco': request.form['endereco'],
            'plano': request.form['plano']
        }

        # Dados da empresa extraídos do formulário
        dados_empresa = {
            'razao_social': request.form['razao_social'],
            'nome_fantasia': request.form['nome_fantasia'],
            'cnpj': request.form['cnpj'],
            'tipo_empresa': request.form['tipo_empresa'],
            'telefone': request.form['telefone'],
            'email_empresarial': request.form['email_empresarial'],
            'inscricao_estadual': request.form['inscricao_estadual'],
            'inscricao_municipal': request.form['inscricao_municipal'],
            'cep_empresa': request.form['cep_empresa'],
            'endereco_empresa': request.form['endereco_empresa']
        }

        # Chama a função do modelo para cadastrar usuário e empresa
        sucesso, mensagem = cadastrar_usuario_empresa(dados_usuario, dados_empresa)
        if sucesso:
            return mensagem
        else:
            return mensagem

    return render_template('cadastro.html')

# Rota para página do painel (acessível apenas para usuários autenticados)
@main.route('/painel')
@login_required
def painel():
    """Exibe o painel do usuário autenticado.

    Returns:
        HTML: Template painel.html renderizado com os dados do usuário.
    """
    return render_template('painel.html', usuario=current_user)

# Rota para logout (acessível apenas para usuários autenticados)
@main.route('/logout')
@login_required
def logout():
    """Faz o logout do usuário e redireciona para a página de login.

    Returns:
        Redireciona para a página de login.
    """
    logout_user()
    return redirect(url_for('main.login_page'))

# Rota para página inicial (Home)
@main.route('/')
def home():
    """Exibe a página inicial da aplicação.

    Returns:
        HTML: Template index.html renderizado.
    """
    return render_template('index.html')

# Rota para página de planos
@main.route('/planos')
def planos():
    """Exibe a página de planos da aplicação.

    Returns:
        HTML: Template planos.html renderizado.
    """
    return render_template('planos.html')

# Rota de webhook para receber mensagens do WhatsApp via Twilio
@main.route('/webhook', methods=['POST'])
def webhook():
    """Processa mensagens recebidas do WhatsApp via Twilio.

    Recebe mensagens, processa com a API DeepSeek e envia resposta de volta via Twilio.

    Returns:
        JSON: Status do processamento da mensagem.
    """
    data = request.form
    message = data.get('Body', '')
    sender = data.get('From', '').replace('whatsapp:', '')

    if not message or not sender:
        return jsonify({"status": "error", "message": "Missing message or sender"}), 400

    response = call_deepseek_api(message)

    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    if not account_sid or not auth_token:
        return jsonify({"status": "error", "message": "Credenciais da Twilio não configuradas"}), 500

    client = Client(account_sid, auth_token)
    client.messages.create(
        from_='whatsapp:+14155238886',
        body=response,
        to=f'whatsapp:{sender}'
    )

    return jsonify({"status": "success", "message": "Message processed"}), 200

# Rota para página de treinamento de IA
@main.route('/treinar_ia')
@login_required
def treinar_ia():
    """Exibe a página de treinamento de IA para usuários autenticados.

    Returns:
        HTML: Template treinar_ia.html renderizado com os dados do usuário.
    """
    return render_template('treinar_ia.html', usuario=current_user)

# Rota para página de configuração da persona da IA
@main.route('/persona_ia', methods=['GET'])
@login_required
def persona_ia():
    """Exibe a página de configuração da persona da IA para usuários autenticados.

    Busca a empresa associada ao usuário e a persona correspondente, se existir.

    Returns:
        HTML: Template persona_ia.html renderizado com os dados do usuário e persona.
    """
    conn = connect_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id FROM empresas WHERE usuario_id = %s", (current_user.id,))
    empresa = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if not empresa:
        logger.error(f"Empresa não encontrada para usuário {current_user.id}")
        return jsonify({'erro': 'Empresa não encontrada'}), 404
    
    persona = get_persona_by_empresa(empresa['id'])
    logger.debug(f"Persona para empresa_id {empresa['id']}: {persona}")
    response = Response(render_template('persona_ia.html', persona=persona, usuario=current_user, empresa_id=empresa['id']))
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    return response

# Rota para salvar a persona da IA
@main.route('/persona_ia/save', methods=['POST'])
@login_required
def save_persona_route():
    """Salva ou atualiza a persona da IA no banco de dados.

    Recebe os dados da persona em JSON e os salva associados à empresa do usuário.

    Returns:
        JSON: Mensagem de sucesso ou erro.
    """
    try:
        data = request.get_json()
        logger.debug(f"Dados recebidos para salvar persona: {data}")
        empresa_id = get_empresa_id_by_usuario(current_user.id)
        
        if not empresa_id:
            logger.error(f"Empresa não encontrada para usuário {current_user.id}")
            return jsonify({'erro': 'Empresa não encontrada'}), 404
        
        logger.debug(f"Módulo de save_persona: {save_persona.__module__}, arquivo: {save_persona.__code__.co_filename}")
        logger.debug(f"Chamando save_persona com empresa_id={empresa_id}, dados={data}")
        sucesso = save_persona(empresa_id, data)
        if sucesso:
            logger.debug(f"Persona salva com sucesso para empresa_id {empresa_id}")
            return jsonify({'mensagem': 'Persona salva com sucesso!'}), 200
        else:
            logger.error(f"Erro ao salvar persona para empresa_id {empresa_id}")
            return jsonify({'erro': 'Erro ao salvar persona'}), 500
    except Exception as e:
        logger.error(f"Erro no endpoint /persona_ia/save: {str(e)}")
        return jsonify({'erro': f'Erro ao salvar: {str(e)}'}), 500

# # Rota temporária para testar a chamada de save_persona
# @main.route('/test_save_persona', methods=['GET'])
# @login_required
# def test_save_persona():
#     """Testa a chamada da função save_persona."""
#     try:
#         empresa_id = get_empresa_id_by_usuario(current_user.id)
#         if not empresa_id:
#             return jsonify({'erro': 'Empresa não encontrada'}), 404
        
#         dados_persona = {
#             'nome_agente': 'Teste',
#             'funcao_agente': 'Vendedor',
#             'idioma': 'Português',
#             'tom_voz': 'Amigável',
#             'estilo_conversacao': 'Chat',
#             'tamanho_resposta': 'Curta',
#             'diretrizes': ['Teste diretriz']
#         }
#         logger.debug(f"Testando save_persona com empresa_id={empresa_id}, dados={dados_persona}")
#         logger.debug(f"Módulo de save_persona: {save_persona.__module__}, arquivo: {save_persona.__code__.co_filename}")
#         sucesso = save_persona(empresa_id, dados_persona)
#         return jsonify({'sucesso': sucesso, 'mensagem': 'Teste concluído'})
#     except Exception as e:
#         logger.error(f"Erro no teste de save_persona: {str(e)}")
#         return jsonify({'erro': f'Erro no teste: {str(e)}'}), 500