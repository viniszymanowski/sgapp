import os
import sys
import logging
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import datetime

# Configurar logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Inicializar o banco de dados
db = SQLAlchemy()

# Modelo de Usuário
class Usuario(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# Modelo de Colheitadeira
class Colheitadeira(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    modelo = db.Column(db.String(100), nullable=False)
    ano = db.Column(db.Integer, nullable=False)
    numero_frota = db.Column(db.String(20), unique=True, nullable=False)
    status = db.Column(db.String(20), default='Ativa')  # Ativa, Em Manutenção, Inativa
    data_cadastro = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    
    # Relacionamentos
    manutencoes_preventivas = db.relationship('ManutencaoPreventiva', backref='colheitadeira', lazy=True)
    manutencoes_corretivas = db.relationship('ManutencaoCorretiva', backref='colheitadeira', lazy=True)
    trocas_oleo = db.relationship('TrocaOleo', backref='colheitadeira', lazy=True)
    registros_horimetro = db.relationship('RegistroHorimetro', backref='colheitadeira', lazy=True)

# Modelo de Manutenção Preventiva
class ManutencaoPreventiva(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    colheitadeira_id = db.Column(db.Integer, db.ForeignKey('colheitadeira.id'), nullable=False)
    descricao = db.Column(db.Text, nullable=False)
    data_programada = db.Column(db.DateTime, nullable=False)
    horimetro_programado = db.Column(db.Float)
    data_realizada = db.Column(db.DateTime)
    horimetro_realizado = db.Column(db.Float)
    observacoes = db.Column(db.Text)
    status = db.Column(db.String(20), default='Pendente')  # Pendente, Realizada, Cancelada

# Modelo de Manutenção Corretiva
class ManutencaoCorretiva(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    colheitadeira_id = db.Column(db.Integer, db.ForeignKey('colheitadeira.id'), nullable=False)
    descricao_falha = db.Column(db.Text, nullable=False)
    data_inicio = db.Column(db.DateTime, nullable=False)
    data_conclusao = db.Column(db.DateTime)
    horimetro = db.Column(db.Float)
    solucao_aplicada = db.Column(db.Text)
    pecas_substituidas = db.Column(db.Text)
    status = db.Column(db.String(20), default='Em Andamento')  # Em Andamento, Concluída, Aguardando Peças

# Modelo de Troca de Óleo
class TrocaOleo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    colheitadeira_id = db.Column(db.Integer, db.ForeignKey('colheitadeira.id'), nullable=False)
    data = db.Column(db.DateTime, nullable=False)
    horimetro = db.Column(db.Float, nullable=False)
    tipo_oleo = db.Column(db.String(100), nullable=False)
    quantidade = db.Column(db.Float, nullable=False)
    observacoes = db.Column(db.Text)

# Modelo de Registro de Horímetro
class RegistroHorimetro(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    colheitadeira_id = db.Column(db.Integer, db.ForeignKey('colheitadeira.id'), nullable=False)
    data = db.Column(db.DateTime, nullable=False)
    valor = db.Column(db.Float, nullable=False)
    horas_motor = db.Column(db.Float)
    observacoes = db.Column(db.Text)

# Modelo de Item de Estoque
class ItemEstoque(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(20), unique=True, nullable=False)
    nome = db.Column(db.String(100), nullable=False)
    categoria = db.Column(db.String(50), nullable=False)
    quantidade = db.Column(db.Float, default=0)
    unidade = db.Column(db.String(20), nullable=False)
    valor_unitario = db.Column(db.Float, nullable=False)
    estoque_minimo = db.Column(db.Float, default=0)
    localizacao = db.Column(db.String(100))
    fornecedor = db.Column(db.String(100))
    data_ultima_compra = db.Column(db.DateTime)
    descricao = db.Column(db.Text)
    observacoes = db.Column(db.Text)
    data_cadastro = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    
    # Relacionamentos
    movimentacoes = db.relationship('MovimentacaoEstoque', backref='item', lazy=True)

# Modelo de Movimentação de Estoque
class MovimentacaoEstoque(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('item_estoque.id'), nullable=False)
    tipo = db.Column(db.String(20), nullable=False)  # Entrada, Saída
    quantidade = db.Column(db.Float, nullable=False)
    data = db.Column(db.DateTime, nullable=False)
    responsavel = db.Column(db.String(100), nullable=False)
    observacao = db.Column(db.Text)

# Função para inicializar o banco de dados
def init_db(app):
    try:
        with app.app_context():
            db.create_all()
            logger.info("Banco de dados inicializado com sucesso")
            
            # Verificar se já existe um usuário admin
            admin = Usuario.query.filter_by(username='admin').first()
            if not admin:
                # Criar usuário admin padrão
                admin = Usuario(username='admin', nome='Administrador', email='admin@example.com')
                admin.set_password('admin123')
                db.session.add(admin)
                db.session.commit()
                logger.info("Usuário admin criado com sucesso")
    except Exception as e:
        logger.error(f"Erro ao inicializar banco de dados: {str(e)}")
        raise
