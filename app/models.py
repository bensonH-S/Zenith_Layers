# Importa o UserMixin do Flask-Login, que fornece métodos padrão pra autenticação de usuários
from flask_login import UserMixin
# Importa a função para conectar ao banco de dados
from database.connection import connect_db
# Importa funções para gerar e verificar hash de senhas
from werkzeug.security import generate_password_hash, check_password_hash
import logging

# Configura logging básico para depuração
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Define a classe Usuario, que representa um usuário no sistema
# Herda de UserMixin pra integrar com o Flask-Login (adiciona métodos como is_authenticated, is_active, etc.)
class Usuario(UserMixin):
    # Método inicializador (construtor) da classe Usuario
    # Recebe os atributos id, nome, email e plano como parâmetros
    def __init__(self, id, nome, email, plano):
        # Atribui o ID do usuário à instância (necessário pro Flask-Login)
        self.id = id
        # Atribui o nome do usuário à instância
        self.nome = nome
        # Atribui o e-mail do usuário à instância
        self.email = email
        # Atribui o plano do usuário à instância (ex.: free, plus, enterprise)
        self.plano = plano

# Função para registrar um usuário no banco de dados (via API)
def registrar_usuario(nome, email, senha):
    """Registra um novo usuário no banco de dados.

    Args:
        nome (str): Nome do usuário.
        email (str): E-mail do usuário.
        senha (str): Senha do usuário (será convertida em hash).

    Returns:
        bool: True se o registro for bem-sucedido, False caso contrário.
    """
    senha_hash = generate_password_hash(senha)
    conn = None
    cursor = None
    try:
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO usuarios (nome, email, senha_hash)
            VALUES (%s, %s, %s)
        """, (nome, email, senha_hash))
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"Erro ao registrar usuário: {str(e)}")
        return False
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# Função para autenticar um usuário
def login_usuario(email, senha):
    """Autentica um usuário verificando email e senha.

    Args:
        email (str): E-mail do usuário.
        senha (str): Senha fornecida para autenticação.

    Returns:
        dict: Dados do usuário se autenticação for bem-sucedida, None caso contrário.
    """
    conn = None
    cursor = None
    try:
        conn = connect_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM usuarios WHERE email = %s", (email,))
        usuario = cursor.fetchone()
        if usuario and check_password_hash(usuario['senha_hash'], senha):
            return usuario
        return None
    except Exception as e:
        logger.error(f"Erro ao autenticar usuário: {str(e)}")
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# Função para autenticar um usuário via formulário web
def login_usuario_web(email, senha):
    """Autentica um usuário via formulário web e retorna um objeto Usuario.

    Args:
        email (str): E-mail do usuário.
        senha (str): Senha fornecida para autenticação.

    Returns:
        Usuario: Objeto Usuario se autenticação for bem-sucedida, None caso contrário.
    """
    usuario_data = login_usuario(email, senha)
    if usuario_data:
        return Usuario(
            id=usuario_data['id'],
            nome=usuario_data['nome'],
            email=usuario_data['email'],
            plano=usuario_data['plano']
        )
    return None

# Função para cadastrar um usuário e sua empresa no banco de dados
def cadastrar_usuario_empresa(dados_usuario, dados_empresa):
    """Cadastra um usuário e sua empresa no banco de dados.

    Args:
        dados_usuario (dict): Dados do usuário (nome, email, senha, cpf, data_nascimento, cep, endereco, plano).
        dados_empresa (dict): Dados da empresa (razao_social, nome_fantasia, cnpj, tipo_empresa, telefone, email_empresarial, inscricao_estadual, inscricao_municipal, cep_empresa, endereco_empresa).

    Returns:
        tuple: (bool, str) - (Sucesso ou falha, Mensagem de resultado).
    """
    conn = None
    cursor = None
    try:
        # Gera o hash da senha
        senha_hash = generate_password_hash(dados_usuario['senha'])
        
        # Conecta ao banco de dados
        conn = connect_db()
        cursor = conn.cursor()

        # Insere o usuário na tabela 'usuarios'
        cursor.execute("""
            INSERT INTO usuarios (nome, email, senha_hash, cpf, data_nascimento, cep, endereco, plano)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            dados_usuario['nome'], dados_usuario['email'], senha_hash,
            dados_usuario.get('cpf', ''), dados_usuario.get('data_nascimento', ''),
            dados_usuario.get('cep', ''), dados_usuario.get('endereco', ''),
            dados_usuario['plano']
        ))
        conn.commit()

        # Pega o ID do usuário recém-inserido
        usuario_id = cursor.lastrowid

        # Insere a empresa vinculada ao usuário na tabela 'empresas', usando cep_empresa e endereco_empresa
        cursor.execute("""
            INSERT INTO empresas (usuario_id, razao_social, nome_fantasia, cnpj, tipo_empresa, cep, endereco, telefone, email_empresarial, inscricao_estadual, inscricao_municipal)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            usuario_id, dados_empresa['razao_social'], dados_empresa['nome_fantasia'],
            dados_empresa['cnpj'], dados_empresa['tipo_empresa'],
            dados_empresa.get('cep_empresa', ''), dados_empresa.get('endereco_empresa', ''),
            dados_empresa['telefone'], dados_empresa['email_empresarial'],
            dados_empresa.get('inscricao_estadual', ''), dados_empresa.get('inscricao_municipal', '')
        ))
        conn.commit()

        return True, f"Cadastro realizado com sucesso para {dados_usuario['nome']} ({dados_usuario['plano']})!"
    except Exception as e:
        logger.error(f"Erro ao cadastrar usuário/empresa: {str(e)}")
        return False, f"Erro ao cadastrar: {str(e)}"
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()