# Importa o módulo os pra manipular pastas e arquivos no sistema operacional
import os

# Define a estrutura de pastas e arquivos do projeto Zenith IA
structure = {
    # Pasta raiz do projeto
    "zenith_ia": [
        # Arquivos e subpastas dentro da pasta app/
        "app/__init__.py",           # Inicialização da aplicação Flask
        "app/routes.py",             # Definição das rotas da aplicação
        "app/utils.py",              # Funções utilitárias (ainda vazio)
        "app/static/.gitkeep",       # Pasta pra arquivos estáticos (CSS, JS, etc.)
        "app/templates/.gitkeep",    # Pasta pra templates HTML
        "app/uploads/.gitkeep",      # Pasta pra uploads de arquivos
        # Arquivos e subpastas dentro da pasta database/
        "database/init_db.sql",      # Script SQL pra inicializar o banco de dados
        "database/connection.py",    # Função pra conectar ao banco de dados
        # Arquivo dentro da pasta model/
        "model/gemma_api.py",        # Integração com a API do modelo Gemma (IA)
        # Arquivo dentro da pasta reports/
        "reports/generate_reports.py",  # Script pra gerar relatórios
        # Arquivo dentro da pasta tests/
        "tests/test_flows.py",       # Testes automatizados do fluxo da aplicação
        # Arquivos na raiz do projeto
        "requirements.txt",          # Dependências do projeto
        "run.py"                     # Script pra rodar a aplicação
    ]
}

# Define o conteúdo inicial de alguns arquivos principais
files_content = {
    # Conteúdo do __init__.py (configuração inicial do Flask)
    "zenith_ia/app/__init__.py": "from flask import Flask\n\ndef create_app():\n    app = Flask(__name__)\n    from .routes import main\n    app.register_blueprint(main)\n    return app\n",
    # Conteúdo do routes.py (rota inicial simples)
    "zenith_ia/app/routes.py": "from flask import Blueprint\n\nmain = Blueprint('main', __name__)\n\n@main.route('/')\ndef home():\n    return 'Zenith IA - MVP rodando com Flask!'\n",
    # Conteúdo do connection.py (conexão com o banco de dados)
    "zenith_ia/database/connection.py": "import mysql.connector\n\ndef connect_db():\n    return mysql.connector.connect(\n        host='localhost',\n        user='root',\n        password='',\n        database='zenith_db'\n    )\n",
    # Conteúdo do run.py (script pra iniciar a aplicação Flask)
    "zenith_ia/run.py": "from app import create_app\n\napp = create_app()\n\nif __name__ == '__main__':\n    app.run(debug=True)\n",
    # Conteúdo do requirements.txt (dependências do projeto)
    "zenith_ia/requirements.txt": "\\\nflask\nmysql-connector-python\npandas\nPyPDF2\nrequests\ntwilio\npython-dotenv\n"
}

# Criação das pastas e arquivos
for base, paths in structure.items():  # Itera sobre a estrutura definida
    for path in paths:  # Itera sobre cada caminho (arquivo ou pasta)
        # Junta o caminho base com o caminho do arquivo (ex.: zenith_ia/app/__init__.py)
        full_path = os.path.join(base, path)
        # Cria as pastas necessárias pro arquivo (exist_ok=True evita erros se a pasta já existir)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        # Abre o arquivo no modo escrita (cria o arquivo se não existir)
        with open(full_path, "w", encoding="utf-8") as f:
            # Pega o conteúdo do arquivo no dicionário files_content (ou vazio se não tiver)
            content = files_content.get(full_path, "")
            # Escreve o conteúdo no arquivo
            f.write(content)

# Mensagem de confirmação após a criação da estrutura
print("✅ Estrutura do projeto Zenith IA criada com sucesso!")