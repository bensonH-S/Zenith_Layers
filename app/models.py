from flask_login import UserMixin
from database.connection import connect_db
from werkzeug.security import generate_password_hash, check_password_hash
import logging
import os
from logging.handlers import RotatingFileHandler

# Configuração de logging
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

class Usuario(UserMixin):
    def __init__(self, id, nome, email, plano):
        self.id = id
        self.nome = nome
        self.email = email
        self.plano = plano

def registrar_usuario(nome, email, senha):
    senha_hash = generate_password_hash(senha)
    conn = None
    cursor = None
    try:
        conn = connect_db()
        if conn is None:
            logger.error("Falha ao conectar ao banco de dados")
            return False
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM usuarios WHERE email = %s", (email,))
        if cursor.fetchone():
            logger.error(f"E-mail {email} já está registrado")
            return False
        cursor.execute("""
            INSERT INTO usuarios (nome, email, senha_hash)
            VALUES (%s, %s, %s)
        """, (nome, email, senha_hash))
        conn.commit()
        logger.info(f"Usuário {email} registrado com sucesso")
        return True
    except Exception as e:
        logger.error(f"Erro ao registrar usuário: {str(e)}")
        return False
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def login_usuario(email, senha):
    conn = None
    cursor = None
    try:
        conn = connect_db()
        if conn is None:
            logger.error("Falha ao conectar ao banco de dados")
            return None
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM usuarios WHERE email = %s", (email,))
        usuario = cursor.fetchone()
        if usuario is None:
            logger.warning(f"Usuário com e-mail {email} não encontrado")
            return None
        if not check_password_hash(usuario['senha_hash'], senha):
            logger.warning(f"Senha incorreta para {email}")
            return None
        logger.info(f"Usuário {email} autenticado com sucesso")
        return usuario
    except Exception as e:
        logger.error(f"Erro ao autenticar usuário: {str(e)}")
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def login_usuario_web(email, senha):
    usuario_data = login_usuario(email, senha)
    if usuario_data:
        return Usuario(
            id=usuario_data['id'],
            nome=usuario_data['nome'],
            email=usuario_data['email'],
            plano=usuario_data['plano']
        )
    return None

def cadastrar_usuario_empresa(dados_usuario, dados_empresa):
    conn = None
    cursor = None
    try:
        senha_hash = generate_password_hash(dados_usuario['senha'])
        conn = connect_db()
        if conn is None:
            logger.error("Falha ao conectar ao banco de dados")
            return False, "Erro ao conectar ao banco de dados"
        conn.autocommit = False
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM usuarios WHERE email = %s", (dados_usuario['email'],))
        if cursor.fetchone():
            return False, f"E-mail {dados_usuario['email']} já está registrado"
        cursor.execute("""
            INSERT INTO usuarios (nome, email, senha_hash, cpf, data_nascimento, cep, endereco, plano)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            dados_usuario['nome'], dados_usuario['email'], senha_hash,
            dados_usuario.get('cpf', ''), dados_usuario.get('data_nascimento', ''),
            dados_usuario.get('cep', ''), dados_usuario.get('endereco', ''),
            dados_usuario['plano']
        ))
        usuario_id = cursor.lastrowid
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
        logger.info(f"Usuário {dados_usuario['email']} e empresa {dados_empresa['razao_social']} cadastrados com sucesso")
        return True, f"Cadastro realizado com sucesso para {dados_usuario['nome']} ({dados_usuario['plano']})!"
    except Exception as e:
        conn.rollback()
        logger.error(f"Erro ao cadastrar usuário/empresa: {str(e)}")
        return False, f"Erro ao cadastrar: {str(e)}"
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def get_empresa_id_by_usuario(usuario_id):
    conn = None
    cursor = None
    try:
        conn = connect_db()
        if conn is None:
            logger.error("Falha ao conectar ao banco de dados")
            return None
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id FROM empresas WHERE usuario_id = %s", (usuario_id,))
        empresa = cursor.fetchone()
        if empresa:
            logger.info(f"Empresa encontrada para usuario_id {usuario_id}: empresa_id {empresa['id']}")
            return empresa['id']
        logger.warning(f"Empresa não encontrada para usuario_id {usuario_id}")
        return None
    except Exception as e:
        logger.error(f"Erro ao buscar empresa: {str(e)}")
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def get_persona_by_empresa(empresa_id):
    conn = None
    cursor = None
    try:
        conn = connect_db()
        if conn is None:
            logger.error("Falha ao conectar ao banco de dados")
            return None
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM persona_ia WHERE empresa_id = %s", (empresa_id,))
        persona = cursor.fetchone()
        if persona:
            logger.info(f"Persona encontrada para empresa_id {empresa_id}")
            return persona
        logger.warning(f"Persona não encontrada para empresa_id {empresa_id}")
        return None
    except Exception as e:
        logger.error(f"Erro ao buscar persona: {str(e)}")
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def save_persona(empresa_id, dados_persona):
    conn = None
    cursor = None
    try:
        conn = connect_db()
        if conn is None:
            logger.error("Falha ao conectar ao banco de dados")
            return False
        cursor = conn.cursor()
        persona = get_persona_by_empresa(empresa_id)
        diretrizes = (dados_persona.get('diretrizes') or [])[:8]
        diretrizes += [''] * (8 - len(diretrizes))
        nome_agente = dados_persona.get('nome_agente', '')
        funcao_agente = dados_persona.get('funcao_agente', 'Assistente Virtual')
        idioma = dados_persona.get('idioma', 'Português')
        tom_voz = dados_persona.get('tom_voz', 'Amigável')
        estilo_conversacao = dados_persona.get('estilo_conversacao', 'Chat')
        tamanho_resposta = dados_persona.get('tamanho_resposta', 'Curta')
        if persona:
            cursor.execute("""
                UPDATE persona_ia
                SET nome_agente = %s, funcao_agente = %s, idioma = %s, tom_voz = %s,
                    estilo_conversacao = %s, tamanho_resposta = %s,
                    diretrizes_1 = %s, diretrizes_2 = %s, diretrizes_3 = %s, diretrizes_4 = %s,
                    diretrizes_5 = %s, diretrizes_6 = %s, diretrizes_7 = %s, diretrizes_8 = %s
                WHERE empresa_id = %s
            """, (
                nome_agente, funcao_agente, idioma, tom_voz,
                estilo_conversacao, tamanho_resposta,
                diretrizes[0] or None, diretrizes[1] or None, diretrizes[2] or None,
                diretrizes[3] or None, diretrizes[4] or None, diretrizes[5] or None,
                diretrizes[6] or None, diretrizes[7] or None, empresa_id
            ))
        else:
            cursor.execute("""
                INSERT INTO persona_ia (
                    empresa_id, nome_agente, funcao_agente, idioma, tom_voz, estilo_conversacao,
                    tamanho_resposta, diretrizes_1, diretrizes_2, diretrizes_3, diretrizes_4,
                    diretrizes_5, diretrizes_6, diretrizes_7, diretrizes_8
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                empresa_id, nome_agente, funcao_agente, idioma, tom_voz,
                estilo_conversacao, tamanho_resposta,
                diretrizes[0] or None, diretrizes[1] or None, diretrizes[2] or None,
                diretrizes[3] or None, diretrizes[4] or None, diretrizes[5] or None,
                diretrizes[6] or None, diretrizes[7] or None
            ))
        conn.commit()
        logger.info(f"Persona salva para empresa_id {empresa_id}")
        return True
    except Exception as e:
        logger.error(f"Erro ao salvar persona: {str(e)}")
        return False
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def save_produtos(produtos=None, update=False):
    conn = None
    cursor = None
    try:
        # Validar entrada
        if not produtos or not isinstance(produtos, list):
            logger.error("Lista de produtos inválida ou vazia")
            return {"success": False, "message": "Nenhum produto válido fornecido", "inserted": 0, "updated": 0, "duplicates": []}

        conn = connect_db()
        if conn is None:
            logger.error("Falha ao conectar ao banco de dados")
            return {"success": False, "message": "Erro ao conectar ao banco de dados", "inserted": 0, "updated": 0, "duplicates": []}
        
        cursor = conn.cursor()
        
        # Verificar duplicatas
        codigos = [produto.get('codigo', '') for produto in produtos if produto.get('codigo')]
        cursor.execute("""
            SELECT codigo FROM produtos WHERE codigo IN (%s)
        """ % ", ".join(["%s"] * len(codigos)), codigos)
        duplicates = [row[0] for row in cursor.fetchall()]
        
        if duplicates and not update:
            logger.warning(f"Produtos duplicados encontrados: {', '.join(duplicates)}")
            return {
                "success": False,
                "message": "Produtos duplicados encontrados",
                "inserted": 0,
                "updated": 0,
                "duplicates": duplicates
            }

        # Processar inserções e atualizações
        inserted_count = 0
        updated_count = 0
        processed_products = []
        
        for produto in produtos:
            codigo = produto.get('codigo', '')
            if not codigo or not isinstance(codigo, str) or not codigo.strip():
                logger.warning(f"Produto sem código válido ignorado: {produto}")
                continue
            
            # Validar e converter tipos
            try:
                valor_unitario = float(produto.get('valor_unitario', 0))
                desconto = float(produto.get('desconto', 0))
                # Calcular valor_venda se não fornecido
                valor_venda = float(produto.get('valor_venda', valor_unitario - desconto))
                quantidade = int(produto.get('quantidade', 0))
                produto_nome = produto.get('produto', '')
                unidade_medida = produto.get('unidade_medida', '')
                
                # Validar campos obrigatórios
                if not produto_nome or not isinstance(produto_nome, str) or not produto_nome.strip():
                    logger.warning(f"Produto {codigo} ignorado: nome do produto ausente ou inválido")
                    continue
                if not unidade_medida or not isinstance(unidade_medida, str) or not unidade_medida.strip():
                    logger.warning(f"Produto {codigo} ignorado: unidade_medida ausente ou inválida")
                    continue
            except (ValueError, TypeError) as e:
                logger.error(f"Erro de tipo no produto {codigo}: {str(e)}")
                continue
            
            # Verificar se o produto já existe
            cursor.execute("""
                SELECT id FROM produtos WHERE codigo = %s
            """, (codigo,))
            existing_product = cursor.fetchone()
            
            if existing_product and update:
                # Atualizar produto existente
                logger.debug(f"Atualizando produto {codigo}")
                cursor.execute("""
                    UPDATE produtos
                    SET produto = %s, valor_unitario = %s, desconto = %s, valor_venda = %s,
                        unidade_medida = %s, quantidade = %s
                    WHERE codigo = %s
                """, (
                    produto_nome, valor_unitario, desconto, valor_venda,
                    unidade_medida, quantidade, codigo
                ))
                updated_count += 1
            elif not existing_product:
                # Inserir novo produto
                logger.debug(f"Inserindo produto {codigo}")
                cursor.execute("""
                    INSERT INTO produtos (
                        codigo, produto, valor_unitario, desconto, valor_venda,
                        unidade_medida, quantidade
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    codigo, produto_nome, valor_unitario, desconto, valor_venda,
                    unidade_medida, quantidade
                ))
                inserted_count += 1
            
            # Adicionar produto processado à lista
            processed_products.append({
                'codigo': codigo,
                'produto': produto_nome,
                'valor_unitario': valor_unitario,
                'desconto': desconto,
                'valor_venda': valor_venda,
                'unidade_medida': unidade_medida,
                'quantidade': quantidade
            })
        
        conn.commit()
        logger.info(f"Produtos processados: {inserted_count} inseridos, {updated_count} atualizados, {len(processed_products)} retornados")
        return {
            "success": True,
            "inserted": inserted_count,
            "updated": updated_count,
            "message": f"{inserted_count} produtos inseridos e {updated_count} produtos atualizados com sucesso!",
            "duplicates": [],
            "data": processed_products
        }
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Erro ao salvar produtos: {str(e)}")
        return {
            "success": False,
            "message": f"Erro ao salvar produtos: {str(e)}",
            "inserted": 0,
            "updated": 0,
            "duplicates": [],
            "data": []
        }
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()