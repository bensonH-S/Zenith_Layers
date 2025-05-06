# Importa o Blueprint pra organizar as rotas da aplicação de forma modular
from flask import Blueprint, request, jsonify
# Importa a função pra gerar hash de senhas de forma segura
from werkzeug.security import generate_password_hash
# Importa a função connect_db pra conectar ao banco de dados
from database.connection import connect_db
# Importa bibliotecas pra fazer requisições à API do DeepSeek e carregar variáveis do .env
import requests
import os
# Importa o Client da Twilio pra enviar mensagens
from twilio.rest import Client


# Cria um blueprint chamado 'main' pra agrupar as rotas da aplicação
main = Blueprint('main', __name__)

# Rota pra registrar um usuário via API (recebe dados em formato JSON)
@main.route('/registro', methods=['POST'])
def registrar_usuario():
    # Pega os dados enviados no corpo da requisição (em JSON)
    data = request.json
    # Extrai os campos nome, email e senha do JSON
    nome = data.get('nome')
    email = data.get('email')
    senha = data.get('senha')

    # Verifica se todos os campos obrigatórios foram preenchidos
    if not all([nome, email, senha]):
        # Retorna um erro 400 (Bad Request) se algum campo estiver faltando
        return jsonify({'erro': 'Todos os campos são obrigatórios'}), 400

    # Gera um hash seguro da senha pra armazenar no banco (não armazena a senha em texto puro)
    senha_hash = generate_password_hash(senha)

    # Inicializa as variáveis de conexão e cursor como None (pra garantir que serão fechadas no finally)
    conn = None
    cursor = None

    try:
        # Conecta ao banco de dados
        conn = connect_db()
        # Cria um cursor pra executar comandos SQL
        cursor = conn.cursor()
        # Insere o novo usuário na tabela 'usuarios'
        cursor.execute("""
            INSERT INTO usuarios (nome, email, senha_hash)
            VALUES (%s, %s, %s)
        """, (nome, email, senha_hash))
        # Confirma a transação no banco de dados
        conn.commit()
        # Retorna uma mensagem de sucesso com status 201 (Created)
        return jsonify({'mensagem': 'Usuário registrado com sucesso!'}), 201

    except Exception as e:
        # Retorna um erro 500 (Internal Server Error) se algo der errado
        return jsonify({'erro': str(e)}), 500

    finally:
        # Garante que o cursor e a conexão sejam fechados, mesmo se houver erro
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# Importa a função pra verificar o hash da senha durante o login
from werkzeug.security import check_password_hash

# Rota pra login de usuário via API (recebe dados em formato JSON)
@main.route('/login', methods=['POST'])
def login_usuario():
    # Pega os dados enviados no corpo da requisição (em JSON)
    data = request.json
    # Extrai os campos email e senha do JSON
    email = data.get('email')
    senha = data.get('senha')

    # Verifica se os campos obrigatórios foram preenchidos
    if not all([email, senha]):
        # Retorna um erro 400 (Bad Request) se algum campo estiver faltando
        return jsonify({'erro': 'Email e senha são obrigatórios'}), 400

    # Inicializa as variáveis de conexão e cursor como None
    conn = None
    cursor = None

    try:
        # Conecta ao banco de dados
        conn = connect_db()
        # Cria um cursor que retorna os resultados como dicionários
        cursor = conn.cursor(dictionary=True)
        # Busca o usuário pelo e-mail
        cursor.execute("SELECT * FROM usuarios WHERE email = %s", (email,))
        # Pega o primeiro resultado (deve ser único, já que o e-mail é único)
        usuario = cursor.fetchone()

        # Verifica se o usuário foi encontrado
        if not usuario:
            # Retorna um erro 404 (Not Found) se o usuário não existir
            return jsonify({'erro': 'Usuário não encontrado'}), 404

        # Verifica se a senha fornecida corresponde ao hash armazenado
        if not check_password_hash(usuario['senha_hash'], senha):
            # Retorna um erro 401 (Unauthorized) se a senha estiver incorreta
            return jsonify({'erro': 'Senha incorreta'}), 401

        # Retorna uma mensagem de sucesso com status 200 (OK)
        return jsonify({'mensagem': f"Bem-vindo, {usuario['nome']}!"}), 200

    except Exception as e:
        # Retorna um erro 500 (Internal Server Error) se algo der errado
        return jsonify({'erro': str(e)}), 500

    finally:
        # Garante que o cursor e a conexão sejam fechados
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# Importa funções pra renderizar templates e redirecionar
from flask import render_template, redirect, url_for

# Rota pra exibir a página de login (método GET)
@main.route('/login', methods=['GET'])
def login_page():
    # Renderiza o template login.html (exibe a página de login pro usuário)
    return render_template('login.html')

# Importa a função login_user pra autenticar usuários e a classe Usuario
from flask_login import login_user
from app.models import Usuario

# Rota pra login via formulário web (método POST)
@main.route('/login-web', methods=['POST'])
def login_web():
    # Pega os dados enviados pelo formulário (e-mail e senha)
    email = request.form.get('email')
    senha = request.form.get('senha')

    # Conecta ao banco de dados
    conn = connect_db()
    # Cria um cursor que retorna os resultados como dicionários
    cursor = conn.cursor(dictionary=True)
    # Busca o usuário pelo e-mail
    cursor.execute("SELECT * FROM usuarios WHERE email = %s", (email,))
    # Pega o primeiro resultado
    usuario = cursor.fetchone()
    # Fecha o cursor e a conexão
    cursor.close()
    conn.close()

    # Verifica se o usuário existe e se a senha está correta
    if usuario and check_password_hash(usuario['senha_hash'], senha):
        # Cria um objeto Usuario com os dados do banco
        user_obj = Usuario(
            id=usuario['id'],
            nome=usuario['nome'],
            email=usuario['email'],
            plano=usuario['plano']
        )
        # Autentica o usuário (inicia a sessão com Flask-Login)
        login_user(user_obj)
        # Redireciona pra página do painel
        return redirect(url_for('main.painel'))

    # Retorna uma mensagem de erro se o login falhar
    return "E-mail ou senha incorretos."

# Importa funções pra lidar com formulários e templates
from flask import render_template, request
from werkzeug.security import generate_password_hash
from database.connection import connect_db

# Rota pra página de cadastro (métodos GET e POST)
@main.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    # Se o método for POST (formulário enviado)
    if request.method == 'POST':
        # Dados do usuário (extraídos do formulário)
        nome = request.form['nome']
        email = request.form['email']
        senha = request.form['senha']
        cpf = request.form['cpf']
        data_nascimento = request.form['data_nascimento']
        cep = request.form['cep']
        endereco = request.form['endereco']
        plano = request.form['plano']
        # Gera um hash seguro da senha
        senha_hash = generate_password_hash(senha)

        # Dados da empresa (extraídos do formulário)
        razao_social = request.form['razao_social']
        nome_fantasia = request.form['nome_fantasia']
        cnpj = request.form['cnpj']
        tipo_empresa = request.form['tipo_empresa']
        telefone = request.form['telefone']
        email_empresarial = request.form['email_empresarial']
        inscricao_estadual = request.form['inscricao_estadual']
        inscricao_municipal = request.form['inscricao_municipal']

        # Conecta ao banco de dados
        conn = connect_db()
        # Cria um cursor pra executar comandos SQL
        cursor = conn.cursor()

        try:
            # Insere o usuário na tabela 'usuarios'
            cursor.execute("""
                INSERT INTO usuarios (nome, email, senha_hash, cpf, data_nascimento, cep, endereco, plano)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (nome, email, senha_hash, cpf, data_nascimento, cep, endereco, plano))
            # Confirma a transação
            conn.commit()

            # Pega o ID do usuário recém-inserido
            usuario_id = cursor.lastrowid

            # Insere a empresa vinculada ao usuário na tabela 'empresas'
            cursor.execute("""
                INSERT INTO empresas (usuario_id, razao_social, nome_fantasia, cnpj, tipo_empresa, cep, endereco, telefone, email_empresarial, inscricao_estadual, inscricao_municipal)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (usuario_id, razao_social, nome_fantasia, cnpj, tipo_empresa, cep, endereco, telefone, email_empresarial, inscricao_estadual, inscricao_municipal))
            # Confirma a transação
            conn.commit()

            # Retorna uma mensagem de sucesso
            return f"Cadastro realizado com sucesso para {nome} ({plano})!"

        except Exception as e:
            # Retorna uma mensagem de erro se algo der errado
            return f"Erro: {str(e)}"

        finally:
            # Fecha o cursor e a conexão
            cursor.close()
            conn.close()

    # Se o método for GET, renderiza o template cadastro.html
    return render_template('cadastro.html')

# Importa decoradores e funções do Flask-Login pra gerenciar autenticação
from flask_login import login_required, current_user

# Rota pra página do painel (acessível apenas pra usuários autenticados)
@main.route('/painel')
@login_required
def painel():
    # Renderiza o template painel.html, passando o usuário atual (current_user)
    return render_template('painel.html', usuario=current_user)

# Importa a função pra fazer logout
from flask_login import logout_user

# Rota pra logout (acessível apenas pra usuários autenticados)
@main.route('/logout')
@login_required
def logout():
    # Faz o logout do usuário (limpa a sessão)
    logout_user()
    # Redireciona pra página de login
    return redirect(url_for('main.login_page'))

# Rota pra página inicial (Home)
@main.route('/')
def home():
    return render_template('index.html')

# Rota pra página de planos
@main.route('/planos')
def planos():
    return render_template('planos.html')

# # Rota de teste pra verificar a integração com o DeepSeek-V3
# @main.route('/test-deepseek', methods=['GET'])
# def test_deepseek():
#     message = "Quero saber mais sobre o plano Plus."
#     response = call_deepseek_api(message)
#     return jsonify({"response": response})

# Rota pra página de treinamento de IA
@main.route('/treinar_ia')
@login_required
def treinar_ia():
    return render_template('treinar_ia.html', usuario=current_user)

# Rota pra página de configuração da persona da IA
@main.route('/persona_ia')
@login_required
def persona_ia():
    return render_template('persona_ia.html', usuario=current_user)