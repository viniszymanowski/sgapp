# Sistema de Controle de Manutenção de Colheitadeiras John Deere

Este é um sistema web completo para controle de manutenção de colheitadeiras agrícolas, com foco especial em colheitadeiras John Deere. O sistema permite o gerenciamento de manutenções preventivas e corretivas, controle de horas de trabalho e motor, trocas de óleo e estoque de peças.

## Funcionalidades

- Cadastro de colheitadeiras (modelo, ano, número de frota)
- Controle de manutenções preventivas baseadas em horas de uso
- Registro de manutenções corretivas (falhas, peças substituídas)
- Controle de trocas de óleo
- Monitoramento de horas de trabalho e motor
- Gestão de estoque de peças e produtos
- Relatórios de custos e histórico de manutenções
- Interface personalizada com tema John Deere

## Requisitos Técnicos

- Python 3.6+
- Flask
- SQLAlchemy
- PostgreSQL (para produção) ou SQLite (para desenvolvimento)
- Gunicorn (para produção)

## Instalação e Configuração

### Ambiente de Desenvolvimento

1. Clone o repositório:
```
git clone https://github.com/seu-usuario/sistema-manutencao-agricola.git
cd sistema-manutencao-agricola
```

2. Crie e ative um ambiente virtual:
```
python -m venv venv
source venv/bin/activate  # No Windows: venv\Scripts\activate
```

3. Instale as dependências:
```
pip install -r requirements.txt
```

4. Inicialize o banco de dados:
```
python init_db.py
```

5. Execute o aplicativo:
```
python app.py
```

6. Acesse o sistema em http://localhost:8000

### Implantação no Render.com

1. Crie uma conta no Render.com

2. Crie um banco de dados PostgreSQL:
   - No dashboard do Render, clique em "New +" e selecione "PostgreSQL"
   - Preencha os campos necessários e selecione o plano gratuito
   - Anote a "Internal Database URL"

3. Crie um Web Service:
   - No dashboard do Render, clique em "New +" e selecione "Web Service"
   - Conecte ao repositório Git ou faça upload do código
   - Configure o serviço:
     - Environment: Python 3
     - Build Command: `pip install -r requirements.txt`
     - Start Command: `gunicorn app:app`
     - Selecione o plano gratuito

4. Configure as variáveis de ambiente:
   - DATABASE_URL: URL do banco de dados PostgreSQL
   - SECRET_KEY: Uma chave secreta para segurança
   - FLASK_ENV: production
   - PYTHONUNBUFFERED: 1

5. Após a implantação, inicialize o banco de dados:
   - Vá para a seção "Shell" no dashboard do Render
   - Execute: `python -c "from app import app, db; app.app_context().push(); db.create_all()"`

## Melhorias de Tratamento de Erros

Esta versão do sistema inclui melhorias significativas no tratamento de erros:

- Logging detalhado para identificar problemas
- Tratamento de exceções em todas as rotas
- Verificação de saúde aprimorada para testar a conexão com o banco de dados
- Página de erro personalizada para mostrar mensagens de erro mais claras
- Correção automática da URL do PostgreSQL (de postgres:// para postgresql://)
- Inicialização automática do banco de dados com dados de exemplo

## Acesso ao Sistema

- URL: Fornecido pelo Render.com após a implantação
- Usuário padrão: admin
- Senha padrão: admin123

**Importante**: Por segurança, altere a senha padrão após o primeiro acesso.

## Suporte e Contato

Para suporte ou dúvidas sobre o sistema, entre em contato com o desenvolvedor.

## Licença

Este projeto é licenciado sob a licença MIT.
