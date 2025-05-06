# Importa o Flask, framework pra criar aplicações web em Python
from flask import Flask
# Importa o LoginManager do Flask-Login, pra gerenciar autenticação de usuários
from flask_login import LoginManager
# Importa o blueprint 'main' do arquivo routes.py (contém as rotas da aplicação)
from app.routes import main
# Importa a classe Usuario do arquivo models.py (representa um usuário no sistema)
from app.models import Usuario
# Importa a função connect_db do arquivo connection.py (conexão com o banco de dados)
from database.connection import connect_db
# Importa bibliotecas pra carregar variáveis de ambiente do .env
from dotenv import load_dotenv
import os

# Carrega as variáveis do arquivo .env
load_dotenv()

# Cria uma instância do LoginManager pra gerenciar autenticação
login_manager = LoginManager()

# Função que cria e configura a aplicação Flask
def create_app():
    # Inicializa a aplicação Flask, passando o nome do módulo atual
    app = Flask(__name__)
    # Define a chave secreta da aplicação (usada pra segurança em sessões e cookies)
    app.secret_key = os.getenv("SECRET_KEY")  # ou use os.getenv("SECRET_KEY") pra carregar de variável de ambiente (mais seguro)
    # Registra o blueprint 'main', que contém as rotas definidas em routes.py
    app.register_blueprint(main)

    # Inicializa o LoginManager na aplicação Flask
    login_manager.init_app(app)
    # Define a rota de login (se o usuário não estiver autenticado, será redirecionado pra essa rota)
    login_manager.login_view = "main.login_page"  # 'main' é o nome do blueprint, 'login_page' é o nome da função da rota

    # Retorna a aplicação Flask configurada
    return app

# Decorador do Flask-Login que define como carregar um usuário a partir do ID (usado pra manter a sessão do usuário)
@login_manager.user_loader
def load_user(user_id):
    # Conecta ao banco de dados usando a função connect_db
    conn = connect_db()
    # Cria um cursor pra executar comandos SQL (dictionary=True retorna os resultados como dicionários)
    cursor = conn.cursor(dictionary=True)
    # Executa uma consulta SQL pra buscar o usuário pelo ID
    cursor.execute("SELECT * FROM usuarios WHERE id = %s", (user_id,))
    # Pega o primeiro resultado da consulta (deve ser único, já que o ID é único)
    user_data = cursor.fetchone()
    # Fecha o cursor pra liberar recursos
    cursor.close()
    # Fecha a conexão com o banco de dados
    conn.close()

    # Se o usuário foi encontrado no banco de dados
    if user_data:
        # Cria e retorna um objeto Usuario com os dados do banco
        return Usuario(
            id=user_data["id"],
            nome=user_data["nome"],
            email=user_data["email"],
            plano=user_data["plano"]
        )
    # Se o usuário não foi encontrado, retorna None (indica que o usuário não existe)
    return None