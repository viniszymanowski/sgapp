import sqlite3
import os
from datetime import datetime, timedelta
import logging
import sys

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Configuração do banco de dados
DATABASE = 'sistema_manutencao.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    # Verificar se o banco de dados já existe
    if os.path.exists(DATABASE):
        logger.info(f"Banco de dados já existe em {DATABASE}")
        return
    
    logger.info("Criando novo banco de dados...")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Criar tabelas
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        nome TEXT NOT NULL,
        tipo TEXT NOT NULL
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS colheitadeiras (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        modelo TEXT NOT NULL,
        numero_serie TEXT UNIQUE NOT NULL,
        ano INTEGER NOT NULL,
        ultima_manutencao TEXT,
        horimetro_atual REAL DEFAULT 0,
        status TEXT DEFAULT 'Operacional'
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS manutencoes_preventivas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        colheitadeira_id INTEGER NOT NULL,
        descricao TEXT NOT NULL,
        data_agendada TEXT NOT NULL,
        data_realizada TEXT,
        horimetro REAL,
        tecnico TEXT,
        status TEXT DEFAULT 'Pendente',
        observacoes TEXT,
        FOREIGN KEY (colheitadeira_id) REFERENCES colheitadeiras (id)
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS manutencoes_corretivas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        colheitadeira_id INTEGER NOT NULL,
        descricao TEXT NOT NULL,
        data_abertura TEXT NOT NULL,
        data_conclusao TEXT,
        horimetro REAL,
        tecnico TEXT,
        status TEXT DEFAULT 'Aberta',
        solucao TEXT,
        FOREIGN KEY (colheitadeira_id) REFERENCES colheitadeiras (id)
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS trocas_oleo (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        colheitadeira_id INTEGER NOT NULL,
        data TEXT NOT NULL,
        horimetro REAL NOT NULL,
        tipo_oleo TEXT NOT NULL,
        quantidade REAL NOT NULL,
        proxima_troca REAL NOT NULL,
        tecnico TEXT,
        observacoes TEXT,
        FOREIGN KEY (colheitadeira_id) REFERENCES colheitadeiras (id)
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS registros_horimetro (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        colheitadeira_id INTEGER NOT NULL,
        data TEXT NOT NULL,
        horimetro REAL NOT NULL,
        operador TEXT,
        observacoes TEXT,
        FOREIGN KEY (colheitadeira_id) REFERENCES colheitadeiras (id)
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS estoque (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        categoria TEXT NOT NULL,
        quantidade INTEGER NOT NULL,
        unidade TEXT NOT NULL,
        preco REAL,
        estoque_minimo INTEGER DEFAULT 5,
        fornecedor TEXT,
        observacoes TEXT
    )
    ''')
    
    # Inserir dados de exemplo
    # Usuários
    cursor.execute("INSERT INTO usuarios (username, password, nome, tipo) VALUES (?, ?, ?, ?)",
                  ('admin', 'admin123', 'Administrador', 'admin'))
    cursor.execute("INSERT INTO usuarios (username, password, nome, tipo) VALUES (?, ?, ?, ?)",
                  ('tecnico', 'tecnico123', 'Técnico de Manutenção', 'tecnico'))
    cursor.execute("INSERT INTO usuarios (username, password, nome, tipo) VALUES (?, ?, ?, ?)",
                  ('operador', 'operador123', 'Operador de Campo', 'operador'))
    
    # Colheitadeiras
    cursor.execute("INSERT INTO colheitadeiras (modelo, numero_serie, ano, ultima_manutencao, horimetro_atual, status) VALUES (?, ?, ?, ?, ?, ?)",
                  ('John Deere S790', 'JD7901234', 2022, '2025-03-15', 350.5, 'Operacional'))
    cursor.execute("INSERT INTO colheitadeiras (modelo, numero_serie, ano, ultima_manutencao, horimetro_atual, status) VALUES (?, ?, ?, ?, ?, ?)",
                  ('John Deere S680', 'JD6805678', 2020, '2025-02-20', 1200.8, 'Operacional'))
    cursor.execute("INSERT INTO colheitadeiras (modelo, numero_serie, ano, ultima_manutencao, horimetro_atual, status) VALUES (?, ?, ?, ?, ?, ?)",
                  ('John Deere T670', 'JDT670123', 2021, '2025-04-01', 800.2, 'Em Manutenção'))
    cursor.execute("INSERT INTO colheitadeiras (modelo, numero_serie, ano, ultima_manutencao, horimetro_atual, status) VALUES (?, ?, ?, ?, ?, ?)",
                  ('John Deere S770', 'JDS770456', 2023, '2025-03-25', 150.0, 'Operacional'))
    cursor.execute("INSERT INTO colheitadeiras (modelo, numero_serie, ano, ultima_manutencao, horimetro_atual, status) VALUES (?, ?, ?, ?, ?, ?)",
                  ('John Deere S760', 'JDS760789', 2021, '2025-04-10', 650.3, 'Operacional'))
    
    # Datas para os registros
    hoje = datetime.now()
    
    # Manutenções Preventivas
    cursor.execute("INSERT INTO manutencoes_preventivas (colheitadeira_id, descricao, data_agendada, data_realizada, horimetro, tecnico, status, observacoes) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                  (1, 'Troca de filtros', (hoje + timedelta(days=5)).strftime('%Y-%m-%d'), None, 400, 'João Silva', 'Pendente', 'Trocar todos os filtros de ar e combustível'))
    cursor.execute("INSERT INTO manutencoes_preventivas (colheitadeira_id, descricao, data_agendada, data_realizada, horimetro, tecnico, status, observacoes) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                  (2, 'Revisão geral', (hoje - timedelta(days=10)).strftime('%Y-%m-%d'), (hoje - timedelta(days=10)).strftime('%Y-%m-%d'), 1250, 'Carlos Santos', 'Realizada', 'Revisão completa realizada conforme manual'))
    cursor.execute("INSERT INTO manutencoes_preventivas (colheitadeira_id, descricao, data_agendada, data_realizada, horimetro, tecnico, status, observacoes) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                  (3, 'Calibração de sensores', (hoje + timedelta(days=3)).strftime('%Y-%m-%d'), None, 850, 'Pedro Oliveira', 'Pendente', 'Calibrar todos os sensores de colheita'))
    cursor.execute("INSERT INTO manutencoes_preventivas (colheitadeira_id, descricao, data_agendada, data_realizada, horimetro, tecnico, status, observacoes) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                  (4, 'Verificação do sistema elétrico', (hoje + timedelta(days=15)).strftime('%Y-%m-%d'), None, 200, 'Roberto Almeida', 'Pendente', 'Verificar todos os componentes elétricos'))
    cursor.execute("INSERT INTO manutencoes_preventivas (colheitadeira_id, descricao, data_agendada, data_realizada, horimetro, tecnico, status, observacoes) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                  (5, 'Lubrificação geral', (hoje - timedelta(days=5)).strftime('%Y-%m-%d'), (hoje - timedelta(days=4)).strftime('%Y-%m-%d'), 700, 'Marcos Souza', 'Realizada', 'Lubrificação realizada em todos os pontos'))
    
    # Manutenções Corretivas
    cursor.execute("INSERT INTO manutencoes_corretivas (colheitadeira_id, descricao, data_abertura, data_conclusao, horimetro, tecnico, status, solucao) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                  (3, 'Falha no sistema hidráulico', (hoje - timedelta(days=2)).strftime('%Y-%m-%d'), None, 800, 'Pedro Oliveira', 'Em Andamento', 'Substituição de mangueiras e válvulas'))
    cursor.execute("INSERT INTO manutencoes_corretivas (colheitadeira_id, descricao, data_abertura, data_conclusao, horimetro, tecnico, status, solucao) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                  (2, 'Problema no sistema elétrico', (hoje - timedelta(days=20)).strftime('%Y-%m-%d'), (hoje - timedelta(days=18)).strftime('%Y-%m-%d'), 1150, 'Carlos Santos', 'Concluída', 'Substituição de fusíveis e reparo na fiação'))
    cursor.execute("INSERT INTO manutencoes_corretivas (colheitadeira_id, descricao, data_abertura, data_conclusao, horimetro, tecnico, status, solucao) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                  (1, 'Vazamento de óleo', (hoje - timedelta(days=15)).strftime('%Y-%m-%d'), (hoje - timedelta(days=14)).strftime('%Y-%m-%d'), 300, 'João Silva', 'Concluída', 'Substituição de vedações e juntas'))
    cursor.execute("INSERT INTO manutencoes_corretivas (colheitadeira_id, descricao, data_abertura, data_conclusao, horimetro, tecnico, status, solucao) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                  (5, 'Problema no motor', (hoje - timedelta(days=30)).strftime('%Y-%m-%d'), (hoje - timedelta(days=25)).strftime('%Y-%m-%d'), 600, 'Marcos Souza', 'Concluída', 'Ajuste de válvulas e substituição de componentes'))
    cursor.execute("INSERT INTO manutencoes_corretivas (colheitadeira_id, descricao, data_abertura, data_conclusao, horimetro, tecnico, status, solucao) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                  (4, 'Falha no sistema de refrigeração', (hoje - timedelta(days=5)).strftime('%Y-%m-%d'), None, 140, 'Roberto Almeida', 'Em Andamento', 'Verificação do radiador e bomba d\'água'))
    
    # Trocas de Óleo
    cursor.execute("INSERT INTO trocas_oleo (colheitadeira_id, data, horimetro, tipo_oleo, quantidade, proxima_troca, tecnico, observacoes) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                  (1, (hoje - timedelta(days=30)).strftime('%Y-%m-%d'), 300, 'John Deere Plus-50 II', 30.5, 800, 'João Silva', 'Troca de óleo e filtro'))
    cursor.execute("INSERT INTO trocas_oleo (colheitadeira_id, data, horimetro, tipo_oleo, quantidade, proxima_troca, tecnico, observacoes) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                  (2, (hoje - timedelta(days=45)).strftime('%Y-%m-%d'), 1100, 'John Deere Plus-50 II', 30.5, 1600, 'Carlos Santos', 'Troca de óleo e filtro'))
    cursor.execute("INSERT INTO trocas_oleo (colheitadeira_id, data, horimetro, tipo_oleo, quantidade, proxima_troca, tecnico, observacoes) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                  (3, (hoje - timedelta(days=60)).strftime('%Y-%m-%d'), 700, 'John Deere Hy-Gard', 25.0, 1200, 'Pedro Oliveira', 'Troca de óleo hidráulico'))
    cursor.execute("INSERT INTO trocas_oleo (colheitadeira_id, data, horimetro, tipo_oleo, quantidade, proxima_troca, tecnico, observacoes) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                  (4, (hoje - timedelta(days=15)).strftime('%Y-%m-%d'), 100, 'John Deere Plus-50 II', 30.5, 600, 'Roberto Almeida', 'Troca de óleo e filtro'))
    cursor.execute("INSERT INTO trocas_oleo (colheitadeira_id, data, horimetro, tipo_oleo, quantidade, proxima_troca, tecnico, observacoes) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                  (5, (hoje - timedelta(days=20)).strftime('%Y-%m-%d'), 600, 'John Deere Plus-50 II', 30.5, 1100, 'Marcos Souza', 'Troca de óleo e filtro'))
    
    # Registros de Horímetro
    cursor.execute("INSERT INTO registros_horimetro (colheitadeira_id, data, horimetro, operador, observacoes) VALUES (?, ?, ?, ?, ?)",
                  (1, (hoje - timedelta(days=1)).strftime('%Y-%m-%d'), 350.5, 'José Pereira', 'Leitura regular'))
    cursor.execute("INSERT INTO registros_horimetro (colheitadeira_id, data, horimetro, operador, observacoes) VALUES (?, ?, ?, ?, ?)",
                  (2, (hoje - timedelta(days=1)).strftime('%Y-%m-%d'), 1200.8, 'Antônio Ferreira', 'Leitura regular'))
    cursor.execute("INSERT INTO registros_horimetro (colheitadeira_id, data, horimetro, operador, observacoes) VALUES (?, ?, ?, ?, ?)",
                  (3, (hoje - timedelta(days=1)).strftime('%Y-%m-%d'), 800.2, 'Roberto Almeida', 'Leitura antes da manutenção'))
    cursor.execute("INSERT INTO registros_horimetro (colheitadeira_id, data, horimetro, operador, observacoes) VALUES (?, ?, ?, ?, ?)",
                  (4, (hoje - timedelta(days=1)).strftime('%Y-%m-%d'), 150.0, 'Marcos Souza', 'Leitura regular'))
    cursor.execute("INSERT INTO registros_horimetro (colheitadeira_id, data, horimetro, operador, observacoes) VALUES (?, ?, ?, ?, ?)",
                  (5, (hoje - timedelta(days=1)).strftime('%Y-%m-%d'), 650.3, 'Paulo Oliveira', 'Leitura regular'))
    
    # Registros históricos de horímetro
    for colheitadeira_id in range(1, 6):
        for i in range(1, 10):
            data = (hoje - timedelta(days=i*10)).strftime('%Y-%m-%d')
            horimetro = 0
            if colheitadeira_id == 1:
                horimetro = 350.5 - (i * 30)
            elif colheitadeira_id == 2:
                horimetro = 1200.8 - (i * 100)
            elif colheitadeira_id == 3:
                horimetro = 800.2 - (i * 70)
            elif colheitadeira_id == 4:
                horimetro = 150.0 - (i * 15)
            elif colheitadeira_id == 5:
                horimetro = 650.3 - (i * 60)
            
            if horimetro > 0:
                cursor.execute("INSERT INTO registros_horimetro (colheitadeira_id, data, horimetro, operador, observacoes) VALUES (?, ?, ?, ?, ?)",
                              (colheitadeira_id, data, horimetro, f'Operador {colheitadeira_id}', 'Leitura histórica'))
    
    # Estoque
    cursor.execute("INSERT INTO estoque (nome, categoria, quantidade, unidade, preco, estoque_minimo, fornecedor, observacoes) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                  ('Filtro de Ar', 'Filtros', 15, 'unidade', 120.50, 5, 'John Deere Brasil', 'Filtro original'))
    cursor.execute("INSERT INTO estoque (nome, categoria, quantidade, unidade, preco, estoque_minimo, fornecedor, observacoes) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                  ('Filtro de Combustível', 'Filtros', 8, 'unidade', 85.75, 5, 'John Deere Brasil', 'Filtro original'))
    cursor.execute("INSERT INTO estoque (nome, categoria, quantidade, unidade, preco, estoque_minimo, fornecedor, observacoes) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                  ('Óleo John Deere Plus-50 II', 'Lubrificantes', 200, 'litro', 45.90, 50, 'John Deere Brasil', 'Óleo de motor premium'))
    cursor.execute("INSERT INTO estoque (nome, categoria, quantidade, unidade, preco, estoque_minimo, fornecedor, observacoes) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                  ('Correia do Motor', 'Peças', 3, 'unidade', 350.00, 2, 'John Deere Brasil', 'Correia original'))
    cursor.execute("INSERT INTO estoque (nome, categoria, quantidade, unidade, preco, estoque_minimo, fornecedor, observacoes) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                  ('Sensor de Umidade', 'Eletrônicos', 2, 'unidade', 1200.00, 1, 'John Deere Brasil', 'Sensor de precisão'))
    cursor.execute("INSERT INTO estoque (nome, categoria, quantidade, unidade, preco, estoque_minimo, fornecedor, observacoes) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                  ('Óleo Hidráulico Hy-Gard', 'Lubrificantes', 150, 'litro', 38.50, 40, 'John Deere Brasil', 'Óleo hidráulico premium'))
    cursor.execute("INSERT INTO estoque (nome, categoria, quantidade, unidade, preco, estoque_minimo, fornecedor, observacoes) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                  ('Filtro de Óleo', 'Filtros', 12, 'unidade', 95.30, 4, 'John Deere Brasil', 'Filtro original'))
    cursor.execute("INSERT INTO estoque (nome, categoria, quantidade, unidade, preco, estoque_minimo, fornecedor, observacoes) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                  ('Kit de Reparo Hidráulico', 'Kits', 5, 'unidade', 450.00, 2, 'John Deere Brasil', 'Kit completo'))
    cursor.execute("INSERT INTO estoque (nome, categoria, quantidade, unidade, preco, estoque_minimo, fornecedor, observacoes) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                  ('Junta do Cabeçote', 'Peças', 4, 'unidade', 180.00, 2, 'John Deere Brasil', 'Junta original'))
    cursor.execute("INSERT INTO estoque (nome, categoria, quantidade, unidade, preco, estoque_minimo, fornecedor, observacoes) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                  ('Bateria 12V', 'Elétricos', 3, 'unidade', 550.00, 1, 'John Deere Brasil', 'Bateria de alta performance'))
    
    conn.commit()
    conn.close()
    logger.info("Banco de dados inicializado com sucesso!")

if __name__ == '__main__':
    init_db()
    logger.info("Script de inicialização do banco de dados concluído!")
