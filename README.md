# Zenith IA - IA Conversacional para Vendas e Suporte em PMEs

## Visão Geral  
**Zenith IA** é uma inteligência artificial conversacional criada para pequenas e médias empresas (PMEs), com o objetivo de automatizar vendas e suporte via WhatsApp.  
O sistema integra o modelo **Gemma-2B** para respostas inteligentes, **Flask** para o painel web, **MySQL** para banco de dados local e **Twilio** para comunicação via WhatsApp.  
Também permite upload de arquivos CSV e PDF para gerenciar produtos e oferece relatórios interativos sobre desempenho e aprendizado da IA.

### Propósito
- Automatizar vendas e suporte, elevando os lucros das PMEs ao "auge" (Zenith).  
- Oferecer relatórios interativos sobre tempo de resposta, precisão, volume de vendas e curva de aprendizado.  
- Modelo de receita (futuro): Assinatura mensal + taxa por venda (valores a definir).

## Tecnologias
- **Flask**: Backend e painel web.  
- **Gemma-2B**: Modelo de IA (executado localmente com ngrok no MVP).  
- **MySQL (XAMPP)**: Banco de dados local (planejado migração para DatabaseMart).  
- **Twilio**: Integração com WhatsApp.  
- **Pandas / PyPDF2**: Processamento de arquivos CSV e PDF.  
- **Render**: Hospedagem da aplicação Flask (MVP).

## Estrutura do Projeto

```plaintext
zenith_ia/
├── app/                          # Aplicação Flask
│   ├── static/                   # Arquivos estáticos (CSS/JS)
│   ├── templates/                # Templates HTML
│   ├── uploads/                  # Uploads de CSV/PDF
│   ├── __init__.py               # Inicialização da aplicação
│   ├── routes.py                 # Rotas da aplicação
│   └── utils.py                  # Funções auxiliares (CSV/PDF)
├── database/                     # Banco de dados
│   ├── init_db.sql               # Script de criação do banco
│   └── connection.py             # Conexão com MySQL
├── model/                        # IA (Gemma-2B)
│   └── gemma_api.py              # Comunicação com API local
├── reports/                      # Relatórios
│   └── generate_reports.py       # Geração dos relatórios
├── tests/                        # Testes da aplicação
│   └── test_flows.py             # Testes de fluxo principais
├── requirements.txt              # Dependências da aplicação
└── run.py                        # Inicialização do Flask
