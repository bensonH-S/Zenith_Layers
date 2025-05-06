# Importa a biblioteca mysql-connector-python pra conectar ao banco de dados MySQL
import mysql.connector
# Importa o módulo os pra acessar variáveis de ambiente
import os
# Importa a função load_dotenv pra carregar variáveis de ambiente de um arquivo .env
from dotenv import load_dotenv

# Carrega as variáveis de ambiente do arquivo .env (ex.: DB_HOST, DB_USER, etc.)
load_dotenv()

# Função que estabelece a conexão com o banco de dados MySQL
def connect_db():
    # Imprime o usuário do banco de dados (pra depuração, pode ser removido em produção)
    print("Conectando como:", os.getenv("DB_USER"))  # DEBUG

    # Retorna uma conexão com o banco de dados usando os parâmetros configurados
    return mysql.connector.connect(
        # Host do banco de dados (ex.: localhost ou um endereço remoto)
        host=os.getenv("DB_HOST"),
        # Usuário do banco de dados (ex.: root ou um usuário específico)
        user=os.getenv("DB_USER"),
        # Senha do usuário do banco de dados
        password=os.getenv("DB_PASSWORD"),
        # Nome do banco de dados a ser usado (ex.: zenith_ia)
        database=os.getenv("DB_NAME"),
        # Usa a implementação pura em Python do MySQL Connector (pra compatibilidade)
        use_pure=True,
        # Define o socket Unix como None (usado apenas em configurações específicas, geralmente em servidores locais)
        unix_socket=None
    )