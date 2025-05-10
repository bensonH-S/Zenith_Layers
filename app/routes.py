from flask import Blueprint, request, jsonify, render_template, redirect, url_for, Response, send_file
import requests
import os
from twilio.rest import Client
from flask_login import login_required, current_user, login_user, logout_user
from app.models import Usuario, registrar_usuario, login_usuario, login_usuario_web, cadastrar_usuario_empresa, get_persona_by_empresa, save_persona, get_empresa_id_by_usuario, save_produtos
from database.connection import connect_db
import logging
from logging.handlers import RotatingFileHandler
# Adiciona suporte para nomes de arquivo seguros e timestamp
from werkzeug.utils import secure_filename
import time

# Configura logging
log_dir = os.path.join(os.path.dirname(__file__), '..', 'log')
os.makedirs(log_dir, exist_ok=True)
log_handler = RotatingFileHandler(
    os.path.join(log_dir, 'system.log'),
    maxBytes=1024*1024,
    backupCount=5
)
log_handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s'))
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(log_handler)

# Configura o blueprint da aplicação
main = Blueprint('main', __name__)

# Define a pasta de arquivos arquivados
ARCHIVE_FOLDER = os.path.join(os.path.dirname(__file__), '..', 'static', 'archive')
os.makedirs(ARCHIVE_FOLDER, exist_ok=True)

# Define a pasta de uploads e formatos permitidos
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), '..', 'static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
ALLOWED_EXTENSIONS = {'xlsx', 'xls'}  # Apenas .xlsx e .xls são aceitos

# Função para validar extensões de arquivo
def allowed_file(filename):
    # Verifica se o arquivo tem extensão e se está na lista permitida
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Função para chamar a API do DeepSeek
def call_deepseek_api(message):
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        logger.error("Chave de API do DeepSeek não encontrada no .env")
        return "Erro: Chave de API do DeepSeek não encontrada no .env"
    endpoint = "https://api.deepseek.com/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "model": "deepseek-chat",
        "messages": [{"role": "system", "content": "Você é um assistente prestativo."}, {"role": "user", "content": message}],
        "max_tokens": 150,
        "temperature": 0.7,
        "stream": False
    }
    try:
        response = requests.post(endpoint, json=payload, headers=headers)
        response.raise_for_status()
        return response.json().get('choices')[0].get('message').get('content')
    except requests.RequestException as e:
        logger.error(f"Erro na API DeepSeek: {str(e)}")
        return f"Erro na API: {str(e)}"

# Rota para upload de arquivos Excel
@main.route('/upload_excel', methods=['POST'])
@login_required
def upload_excel():
    # Verifica se um arquivo foi enviado
    if 'file' not in request.files:
        logger.error(f"Arquivo ausente na requisição /upload_excel para usuário {current_user.email}")
        return jsonify({'success': False, 'message': 'Nenhum arquivo enviado'}), 400
    
    file = request.files['file']
    # Verifica se o nome do arquivo está vazio
    if file.filename == '':
        logger.error(f"Nenhum arquivo selecionado na requisição /upload_excel para usuário {current_user.email}")
        return jsonify({'success': False, 'message': 'Nenhum arquivo selecionado'}), 400
    
    # Valida o tipo de arquivo
    if not allowed_file(file.filename):
        logger.error(f"Formato de arquivo inválido na requisição /upload_excel para usuário {current_user.email}")
        return jsonify({'success': False, 'message': 'Formato inválido, use .xlsx ou .xls'}), 400
    
    if file:
        # Obtém o ID da empresa do usuário autenticado
        empresa_id = get_empresa_id_by_usuario(current_user.id)
        if not empresa_id:
            logger.error(f"Empresa não encontrada para usuário {current_user.email}")
            return jsonify({'success': False, 'message': 'Empresa não encontrada'}), 404
        
        # Gera um nome único com timestamp e ID da empresa
        timestamp = str(int(time.time()))
        filename = secure_filename(f"{empresa_id}_{timestamp}_{file.filename}")
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        
        # Verifica o tamanho do arquivo (máximo 10MB)
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        if file_size > 10 * 1024 * 1024:  # 10MB
            logger.error(f"Arquivo muito grande na requisição /upload_excel para usuário {current_user.email}")
            return jsonify({'success': False, 'message': 'Arquivo excede 10MB'}), 400
        file.seek(0)
        
        # Salva o arquivo no servidor
        file.save(file_path)
        logger.info(f"Arquivo {filename} salvo com sucesso para usuário {current_user.email}")
        return jsonify({'success': True, 'message': 'Arquivo enviado com sucesso!', 'filename': filename}), 200

@main.route('/registro', methods=['POST'])
def registrar_usuario_route():
    data = request.get_json()
    if not data:
        logger.error("Dados JSON ausentes na requisição /registro")
        return jsonify({'success': False, 'message': 'Dados JSON ausentes'}), 400
    nome = data.get('nome')
    email = data.get('email')
    senha = data.get('senha')
    if not all([nome, email, senha]):
        logger.error("Campos obrigatórios ausentes na requisição /registro")
        return jsonify({'success': False, 'message': 'Todos os campos são obrigatórios'}), 400
    sucesso = registrar_usuario(nome, email, senha)
    if sucesso:
        logger.info(f"Usuário {email} registrado com sucesso via /registro")
        return jsonify({'success': True, 'message': 'Usuário registrado com sucesso!'}), 201
    logger.error(f"Erro ao registrar usuário {email}: e-mail já pode estar em uso")
    return jsonify({'success': False, 'message': 'Erro ao registrar usuário, e-mail já pode estar em uso'}), 400

@main.route('/login', methods=['POST'])
def login_usuario_route():
    data = request.get_json()
    if not data:
        logger.error("Dados JSON ausentes na requisição /login")
        return jsonify({'success': False, 'message': 'Dados JSON ausentes'}), 400
    email = data.get('email')
    senha = data.get('senha')
    if not all([email, senha]):
        logger.error("Campos obrigatórios ausentes na requisição /login")
        return jsonify({'success': False, 'message': 'Email e senha são obrigatórios'}), 400
    usuario = login_usuario(email, senha)
    if not usuario:
        logger.warning(f"Falha na autenticação via /login para {email}")
        return jsonify({'success': False, 'message': 'Usuário não encontrado ou senha incorreta'}), 401
    logger.info(f"Usuário {email} autenticado com sucesso via /login")
    return jsonify({'success': True, 'message': f"Bem-vindo, {usuario['nome']}!"}), 200

@main.route('/login', methods=['GET'])
def login_page():
    logger.info("Renderizando página de login")
    return render_template('login.html')

@main.route('/login-web', methods=['POST'])
def login_web():
    email = request.form.get('email')
    senha = request.form.get('senha')
    if not all([email, senha]):
        logger.error("E-mail ou senha ausentes na requisição /login-web")
        return jsonify({'success': False, 'message': 'E-mail e senha são obrigatórios'}), 400
    try:
        user_obj = login_usuario_web(email, senha)
        if user_obj:
            login_user(user_obj)
            logger.info(f"Usuário {email} autenticado com sucesso via /login-web")
            return jsonify({'success': True, 'message': 'Autenticação efetuada com sucesso!'}), 200
        logger.warning(f"Falha na autenticação via /login-web para {email}: e-mail ou senha incorretos")
        return jsonify({'success': False, 'message': 'E-mail ou senha incorretos'}), 401
    except Exception as e:
        logger.error(f"Erro ao autenticar usuário via /login-web: {str(e)}")
        return jsonify({'success': False, 'message': f'Erro ao autenticar: {str(e)}'}), 500

@main.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        try:
            data = request.get_json()
            if not data:
                logger.error("Dados JSON ausentes na requisição /cadastro")
                return jsonify({'success': False, 'message': 'Dados JSON ausentes'}), 400
            dados_usuario = data.get('dados_usuario', {})
            dados_empresa = data.get('dados_empresa', {})
            if not all([dados_usuario.get(key) for key in ['nome', 'email', 'senha', 'plano']]) or not all([dados_empresa.get(key) for key in ['razao_social', 'cnpj']]):
                logger.error("Campos obrigatórios ausentes na requisição /cadastro")
                return jsonify({'success': False, 'message': 'Todos os campos obrigatórios devem ser preenchidos'}), 400
            sucesso, mensagem = cadastrar_usuario_empresa(dados_usuario, dados_empresa)
            if sucesso:
                logger.info(f"Usuário {dados_usuario['email']} e empresa {dados_empresa['razao_social']} cadastrados com sucesso")
                return jsonify({'success': True, 'message': mensagem}), 201
            logger.error(f"Erro ao cadastrar usuário/empresa: {mensagem}")
            return jsonify({'success': False, 'message': mensagem}), 400
        except Exception as e:
            logger.error(f"Erro no endpoint /cadastro: {str(e)}")
            return jsonify({'success': False, 'message': f'Erro ao cadastrar: {str(e)}'}), 500
    logger.info("Renderizando página de cadastro")
    return render_template('cadastro.html')

@main.route('/painel')
@login_required
def painel():
    logger.info(f"Renderizando painel para usuário {current_user.email}")
    return render_template('painel.html', usuario=current_user)

@main.route('/acoes')
@login_required
def acoes():
    try:
        logger.info(f"Tentando renderizar página de ações para usuário {current_user.email} (ID: {current_user.id})")
        empresa_id = get_empresa_id_by_usuario(current_user.id)
        if not empresa_id:
            logger.error(f"Empresa não encontrada para usuário {current_user.email}")
            return jsonify({'success': False, 'message': 'Empresa não encontrada'}), 404
        return render_template('acoes.html', usuario=current_user, empresa_id=empresa_id)
    except Exception as e:
        logger.error(f"Erro ao renderizar página de ações para usuário {current_user.email}: {str(e)}")
        return jsonify({'success': False, 'message': f'Erro ao carregar página de ações: {str(e)}'}), 500

@main.route('/upload_produtos', methods=['POST'])
@login_required
def upload_produtos():
    try:
        data = request.get_json()
        if not data:
            logger.warning(f"Dados JSON ausentes na requisição /upload_produtos para usuário {current_user.email}")
            return jsonify({'success': False, 'message': 'Nenhum dado fornecido'}), 400
        
        update = data.get('update', False)
        produtos = data.get('produtos', [])
        
        if not produtos:
            logger.warning(f"Lista de produtos vazia na requisição /upload_produtos para usuário {current_user.email}")
            return jsonify({'success': False, 'message': 'Lista de produtos vazia'}), 400
        
        result = save_produtos(produtos, update)
        logger.info(f"Upload de produtos processado para usuário {current_user.email}: {result.get('message')}")
        return jsonify(result), 200 if result['success'] or result.get('duplicates') else 500
    except Exception as e:
        logger.error(f"Erro ao processar upload de produtos para usuário {current_user.email}: {str(e)}")
        return jsonify({'success': False, 'message': f'Erro ao processar: {str(e)}', 'inserted': 0, 'updated': 0, 'duplicates': []}), 500

@main.route('/download_json_template')
@login_required
def download_json_template():
    try:
        json_content = '''[
            {
                "id": 1,
                "codigo": "COD001",
                "produto": "Produto Exemplo",
                "valor_unitario": 100.00,
                "desconto": 10,
                "valor_venda": 90.00,
                "unidade_medida": "un",
                "quantidade": 5
            }
        ]'''
        file_path = os.path.join(ARCHIVE_FOLDER, 'produtos_vendas_template.json')
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(json_content)
        logger.info(f"Arquivo JSON gerado: {file_path}")
        return send_file(file_path, as_attachment=True, download_name='produtos_vendas_template.json')
    except Exception as e:
        logger.error(f"Erro ao gerar arquivo JSON para usuário {current_user.email}: {str(e)}")
        return jsonify({'success': False, 'message': f'Erro ao gerar template JSON: {str(e)}'}), 500

@main.route('/download_csv_template')
@login_required
def download_csv_template():
    try:
        csv_content = '''"id","codigo","produto","valor_unitario","desconto","valor_venda","unidade_medida","quantidade"
1,"COD001","Produto Exemplo",100.00,10,90.00,"un",5'''
        file_path = os.path.join(ARCHIVE_FOLDER, 'produtos_vendas_template.csv')
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(csv_content)
        logger.info(f"Arquivo CSV gerado: {file_path}")
        return send_file(file_path, as_attachment=True, download_name='produtos_vendas_template.csv')
    except Exception as e:
        logger.error(f"Erro ao gerar arquivo CSV para usuário {current_user.email}: {str(e)}")
        return jsonify({'success': False, 'message': f'Erro ao gerar template CSV: {str(e)}'}), 500

@main.route('/logout')
@login_required
def logout():
    logger.info(f"Usuário {current_user.email} fez logout")
    logout_user()
    return redirect(url_for('main.login_page'))

@main.route('/')
def home():
    logger.info("Renderizando página inicial")
    return render_template('index.html')

@main.route('/planos')
def planos():
    logger.info("Renderizando página de planos")
    return render_template('planos.html')

@main.route('/webhook', methods=['POST'])
def webhook():
    data = request.form
    message = data.get('Body', '')
    sender = data.get('From', '').replace('whatsapp:', '')
    if not message or not sender:
        logger.error("Mensagem ou remetente ausentes na requisição /webhook")
        return jsonify({'success': False, 'message': 'Missing message or sender'}), 400
    response = call_deepseek_api(message)
    account_sid = os.getenv('TWILIO_ACCOUNT_SID')
    auth_token = os.getenv('TWILIO_AUTH_TOKEN')
    if not account_sid or not auth_token:
        logger.error("Credenciais da Twilio não configuradas")
        return jsonify({'success': False, 'message': 'Credenciais da Twilio não configuradas'}), 500
    try:
        client = Client(account_sid, auth_token)
        client.messages.create(
            from_='whatsapp:+14155238886',
            body=response,
            to=f'whatsapp:{sender}'
        )
        logger.info(f"Mensagem processada e enviada para {sender}")
        return jsonify({'success': True, 'message': 'Message processed'}), 200
    except Exception as e:
        logger.error(f"Erro ao enviar mensagem via Twilio: {str(e)}")
        return jsonify({'success': False, 'message': f'Erro ao enviar mensagem: {str(e)}'}), 500

@main.route('/treinar_ia')
@login_required
def treinar_ia():
    logger.info(f"Renderizando página de treinamento de IA para usuário {current_user.email}")
    return render_template('treinar_ia.html', usuario=current_user)

@main.route('/persona_ia', methods=['GET'])
@login_required
def persona_ia():
    try:
        empresa_id = get_empresa_id_by_usuario(current_user.id)
        if not empresa_id:
            logger.error(f"Empresa não encontrada para usuário {current_user.id}")
            return jsonify({'success': False, 'message': 'Empresa não encontrada'}), 404
        persona = get_persona_by_empresa(empresa_id)
        response = Response(
            render_template('persona_ia.html', persona=persona, usuario=current_user, empresa_id=empresa_id)
        )
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        logger.info(f"Renderizando página de persona para usuário {current_user.email}")
        return response
    except Exception as e:
        logger.error(f"Erro no endpoint /persona_ia: {str(e)}")
        return jsonify({'success': False, 'message': f'Erro ao carregar persona: {str(e)}'}), 500

@main.route('/persona_ia/save', methods=['POST'])
@login_required
def save_persona_route():
    try:
        data = request.get_json()
        empresa_id = get_empresa_id_by_usuario(current_user.id)
        if not empresa_id:
            logger.error(f"Empresa não encontrada para usuário {current_user.id}")
            return jsonify({'success': False, 'message': 'Empresa não encontrada'}), 404
        sucesso = save_persona(empresa_id, data)
        if sucesso:
            logger.info(f"Persona salva para empresa_id {empresa_id} pelo usuário {current_user.email}")
            return jsonify({'success': True, 'message': 'Persona salva com sucesso!'}), 200
        logger.error(f"Erro ao salvar persona para empresa_id {empresa_id}")
        return jsonify({'success': False, 'message': 'Erro ao salvar persona'}), 500
    except Exception as e:
        logger.error(f"Erro no endpoint /persona_ia/save: {str(e)}")
        return jsonify({'success': False, 'message': f'Erro ao salvar: {str(e)}'}), 500