# Importa o UserMixin do Flask-Login, que fornece métodos padrão pra autenticação de usuários
from flask_login import UserMixin

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