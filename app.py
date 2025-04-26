import os
import sys
import logging
from flask import Flask, render_template, redirect, url_for, flash, request
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import datetime

# Configurar logging detalhado
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Criar aplicação Flask com tratamento de erros aprimorado
app = Flask(__name__)

# Carregar configurações
try:
    from config import Config
    app.config.from_object(Config)
    logger.info("Configurações carregadas com sucesso")
except Exception as e:
    logger.error(f"Erro ao carregar configurações: {str(e)}")
    # Configuração de fallback
    app.config['SECRET_KEY'] = 'chave_secreta_temporaria'
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///manutencao.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Corrigir URL do PostgreSQL se necessário
    if app.config['SQLALCHEMY_DATABASE_URI'].startswith('postgres://'):
        app.config['SQLALCHEMY_DATABASE_URI'] = app.config['SQLALCHEMY_DATABASE_URI'].replace('postgres://', 'postgresql://', 1)
        logger.info("URL do PostgreSQL corrigida")

# Inicializar o banco de dados
try:
    from models import db, Usuario, Colheitadeira, ManutencaoPreventiva, ManutencaoCorretiva, TrocaOleo, RegistroHorimetro, ItemEstoque, MovimentacaoEstoque
    db.init_app(app)
    logger.info("Banco de dados inicializado com sucesso")
except Exception as e:
    logger.error(f"Erro ao inicializar banco de dados: {str(e)}")
    raise

# Configurar o gerenciador de login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    try:
        return Usuario.query.get(int(user_id))
    except Exception as e:
        logger.error(f"Erro ao carregar usuário: {str(e)}")
        return None

# Criar todas as tabelas do banco de dados
with app.app_context():
    try:
        db.create_all()
        logger.info("Tabelas do banco de dados criadas com sucesso")
        
        # Verificar se já existe um usuário admin
        admin = Usuario.query.filter_by(username='admin').first()
        if not admin:
            # Criar usuário admin padrão
            admin = Usuario(username='admin', nome='Administrador', email='admin@example.com')
            admin.set_password('admin123')
            db.session.add(admin)
            
            # Criar usuários adicionais
            tecnico = Usuario(username='tecnico', nome='Técnico de Manutenção', email='tecnico@example.com', cargo='Técnico')
            tecnico.set_password('tecnico123')
            db.session.add(tecnico)
            
            operador = Usuario(username='operador', nome='Operador de Campo', email='operador@example.com', cargo='Operador')
            operador.set_password('operador123')
            db.session.add(operador)
            
            db.session.commit()
            logger.info("Usuários criados com sucesso")
            
            # Importar e executar a função de criação de dados de exemplo
            try:
                from init_db import criar_dados_exemplo
                criar_dados_exemplo()
                logger.info("Dados de exemplo criados com sucesso")
            except Exception as e:
                logger.error(f"Erro ao criar dados de exemplo: {str(e)}")
    except Exception as e:
        logger.error(f"Erro ao criar tabelas ou usuário admin: {str(e)}")
        # Não levante a exceção aqui para permitir que a aplicação continue

# Rota de verificação de saúde para o Render.com
@app.route('/health')
def health_check():
    try:
        # Verificar conexão com o banco de dados
        Usuario.query.first()
        return "OK", 200
    except Exception as e:
        logger.error(f"Erro na verificação de saúde: {str(e)}")
        return f"Erro: {str(e)}", 500

# Rotas de autenticação
@app.route('/')
@app.route('/login', methods=['GET', 'POST'])
def login():
    try:
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
        
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            
            user = Usuario.query.filter_by(username=username).first()
            
            if user and user.check_password(password):
                login_user(user)
                return redirect(url_for('dashboard'))
            else:
                flash('Usuário ou senha inválidos')
        
        return render_template('login.html')
    except Exception as e:
        logger.error(f"Erro na rota de login: {str(e)}")
        return render_template('error.html', error=str(e))

@app.route('/logout')
@login_required
def logout():
    try:
        logout_user()
        return redirect(url_for('login'))
    except Exception as e:
        logger.error(f"Erro na rota de logout: {str(e)}")
        return render_template('error.html', error=str(e))

# Dashboard
@app.route('/dashboard')
@login_required
def dashboard():
    try:
        colheitadeiras_ativas = Colheitadeira.query.filter_by(status='Ativa').count()
        colheitadeiras_manutencao = Colheitadeira.query.filter_by(status='Em Manutenção').count()
        colheitadeiras_inativas = Colheitadeira.query.filter_by(status='Inativa').count()
        
        manutencoes_preventivas = ManutencaoPreventiva.query.filter_by(status='Pendente').count()
        manutencoes_corretivas = ManutencaoCorretiva.query.filter_by(status='Em Andamento').count()
        
        return render_template('dashboard.html', 
                              colheitadeiras_ativas=colheitadeiras_ativas,
                              colheitadeiras_manutencao=colheitadeiras_manutencao,
                              colheitadeiras_inativas=colheitadeiras_inativas,
                              manutencoes_preventivas=manutencoes_preventivas,
                              manutencoes_corretivas=manutencoes_corretivas)
    except Exception as e:
        logger.error(f"Erro na rota de dashboard: {str(e)}")
        return render_template('error.html', error=str(e))

# Rotas para Colheitadeiras
@app.route('/colheitadeiras')
@login_required
def listar_colheitadeiras():
    try:
        colheitadeiras = Colheitadeira.query.all()
        return render_template('colheitadeiras/listar.html', colheitadeiras=colheitadeiras)
    except Exception as e:
        logger.error(f"Erro ao listar colheitadeiras: {str(e)}")
        return render_template('error.html', error=str(e))

@app.route('/colheitadeiras/adicionar', methods=['GET', 'POST'])
@login_required
def adicionar_colheitadeira():
    try:
        if request.method == 'POST':
            modelo = request.form['modelo']
            ano = request.form['ano']
            numero_frota = request.form['numero_frota']
            status = request.form['status']
            
            colheitadeira = Colheitadeira(modelo=modelo, ano=ano, numero_frota=numero_frota, status=status)
            db.session.add(colheitadeira)
            db.session.commit()
            
            flash('Colheitadeira adicionada com sucesso!')
            return redirect(url_for('listar_colheitadeiras'))
        
        return render_template('colheitadeiras/adicionar.html')
    except Exception as e:
        logger.error(f"Erro ao adicionar colheitadeira: {str(e)}")
        return render_template('error.html', error=str(e))

@app.route('/colheitadeiras/<int:id>')
@login_required
def visualizar_colheitadeira(id):
    try:
        colheitadeira = Colheitadeira.query.get_or_404(id)
        manutencoes_preventivas = ManutencaoPreventiva.query.filter_by(colheitadeira_id=id).all()
        manutencoes_corretivas = ManutencaoCorretiva.query.filter_by(colheitadeira_id=id).all()
        trocas_oleo = TrocaOleo.query.filter_by(colheitadeira_id=id).all()
        registros_horimetro = RegistroHorimetro.query.filter_by(colheitadeira_id=id).order_by(RegistroHorimetro.data.desc()).all()
        
        return render_template('colheitadeiras/visualizar.html', 
                              colheitadeira=colheitadeira,
                              manutencoes_preventivas=manutencoes_preventivas,
                              manutencoes_corretivas=manutencoes_corretivas,
                              trocas_oleo=trocas_oleo,
                              registros_horimetro=registros_horimetro)
    except Exception as e:
        logger.error(f"Erro ao visualizar colheitadeira: {str(e)}")
        return render_template('error.html', error=str(e))

@app.route('/colheitadeiras/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_colheitadeira(id):
    try:
        colheitadeira = Colheitadeira.query.get_or_404(id)
        
        if request.method == 'POST':
            colheitadeira.modelo = request.form['modelo']
            colheitadeira.ano = request.form['ano']
            colheitadeira.numero_frota = request.form['numero_frota']
            colheitadeira.status = request.form['status']
            
            db.session.commit()
            flash('Colheitadeira atualizada com sucesso!')
            return redirect(url_for('listar_colheitadeiras'))
        
        return render_template('colheitadeiras/editar.html', colheitadeira=colheitadeira)
    except Exception as e:
        logger.error(f"Erro ao editar colheitadeira: {str(e)}")
        return render_template('error.html', error=str(e))

# Rotas para Manutenções Preventivas
@app.route('/manutencoes/preventivas')
@login_required
def listar_manutencoes_preventivas():
    try:
        manutencoes = ManutencaoPreventiva.query.all()
        return render_template('manutencoes/preventivas/listar.html', manutencoes=manutencoes)
    except Exception as e:
        logger.error(f"Erro ao listar manutenções preventivas: {str(e)}")
        return render_template('error.html', error=str(e))

@app.route('/manutencoes/preventivas/adicionar', methods=['GET', 'POST'])
@login_required
def adicionar_manutencao_preventiva():
    try:
        colheitadeiras = Colheitadeira.query.all()
        
        if request.method == 'POST':
            colheitadeira_id = request.form['colheitadeira_id']
            descricao = request.form['descricao']
            data_programada = datetime.datetime.strptime(request.form['data_programada'], '%Y-%m-%d')
            horimetro_programado = request.form['horimetro_programado']
            
            manutencao = ManutencaoPreventiva(
                colheitadeira_id=colheitadeira_id,
                descricao=descricao,
                data_programada=data_programada,
                horimetro_programado=horimetro_programado,
                status='Pendente'
            )
            
            db.session.add(manutencao)
            db.session.commit()
            
            flash('Manutenção preventiva programada com sucesso!')
            return redirect(url_for('listar_manutencoes_preventivas'))
        
        return render_template('manutencoes/preventivas/adicionar.html', colheitadeiras=colheitadeiras)
    except Exception as e:
        logger.error(f"Erro ao adicionar manutenção preventiva: {str(e)}")
        return render_template('error.html', error=str(e))

@app.route('/manutencoes/preventivas/realizar/<int:id>', methods=['GET', 'POST'])
@login_required
def realizar_manutencao_preventiva(id):
    try:
        manutencao = ManutencaoPreventiva.query.get_or_404(id)
        
        if request.method == 'POST':
            manutencao.data_realizada = datetime.datetime.strptime(request.form['data_realizada'], '%Y-%m-%d')
            manutencao.horimetro_realizado = request.form['horimetro_realizado']
            manutencao.observacoes = request.form['observacoes']
            manutencao.status = 'Realizada'
            
            # Atualizar status da colheitadeira se necessário
            if request.form.get('atualizar_status') == 'sim':
                colheitadeira = Colheitadeira.query.get(manutencao.colheitadeira_id)
                colheitadeira.status = 'Ativa'
                db.session.commit()
            
            db.session.commit()
            flash('Manutenção preventiva realizada com sucesso!')
            return redirect(url_for('listar_manutencoes_preventivas'))
        
        return render_template('manutencoes/preventivas/realizar.html', manutencao=manutencao)
    except Exception as e:
        logger.error(f"Erro ao realizar manutenção preventiva: {str(e)}")
        return render_template('error.html', error=str(e))

# Rotas para Manutenções Corretivas
@app.route('/manutencoes/corretivas')
@login_required
def listar_manutencoes_corretivas():
    try:
        manutencoes = ManutencaoCorretiva.query.all()
        return render_template('manutencoes/corretivas/listar.html', manutencoes=manutencoes)
    except Exception as e:
        logger.error(f"Erro ao listar manutenções corretivas: {str(e)}")
        return render_template('error.html', error=str(e))

@app.route('/manutencoes/corretivas/adicionar', methods=['GET', 'POST'])
@login_required
def adicionar_manutencao_corretiva():
    try:
        colheitadeiras = Colheitadeira.query.all()
        
        if request.method == 'POST':
            colheitadeira_id = request.form['colheitadeira_id']
            descricao_falha = request.form['descricao_falha']
            data_inicio = datetime.datetime.strptime(request.form['data_inicio'], '%Y-%m-%d')
            horimetro = request.form['horimetro']
            
            manutencao = ManutencaoCorretiva(
                colheitadeira_id=colheitadeira_id,
                descricao_falha=descricao_falha,
                data_inicio=data_inicio,
                horimetro=horimetro,
                status='Em Andamento'
            )
            
            # Atualizar status da colheitadeira
            colheitadeira = Colheitadeira.query.get(colheitadeira_id)
            colheitadeira.status = 'Em Manutenção'
            
            db.session.add(manutencao)
            db.session.commit()
            
            flash('Manutenção corretiva registrada com sucesso!')
            return redirect(url_for('listar_manutencoes_corretivas'))
        
        return render_template('manutencoes/corretivas/adicionar.html', colheitadeiras=colheitadeiras)
    except Exception as e:
        logger.error(f"Erro ao adicionar manutenção corretiva: {str(e)}")
        return render_template('error.html', error=str(e))

@app.route('/manutencoes/corretivas/concluir/<int:id>', methods=['GET', 'POST'])
@login_required
def concluir_manutencao_corretiva(id):
    try:
        manutencao = ManutencaoCorretiva.query.get_or_404(id)
        
        if request.method == 'POST':
            manutencao.solucao_aplicada = request.form['solucao_aplicada']
            manutencao.pecas_substituidas = request.form['pecas_substituidas']
            manutencao.data_conclusao = datetime.datetime.strptime(request.form['data_conclusao'], '%Y-%m-%d')
            manutencao.status = 'Concluída'
            
            # Atualizar status da colheitadeira
            colheitadeira = Colheitadeira.query.get(manutencao.colheitadeira_id)
            colheitadeira.status = 'Ativa'
            
            db.session.commit()
            flash('Manutenção corretiva concluída com sucesso!')
            return redirect(url_for('listar_manutencoes_corretivas'))
        
        return render_template('manutencoes/corretivas/concluir.html', manutencao=manutencao)
    except Exception as e:
        logger.error(f"Erro ao concluir manutenção corretiva: {str(e)}")
        return render_template('error.html', error=str(e))

# Rotas para Trocas de Óleo
@app.route('/trocas-oleo')
@login_required
def listar_trocas_oleo():
    try:
        trocas = TrocaOleo.query.all()
        return render_template('trocas_oleo/listar.html', trocas=trocas)
    except Exception as e:
        logger.error(f"Erro ao listar trocas de óleo: {str(e)}")
        return render_template('error.html', error=str(e))

@app.route('/trocas-oleo/adicionar', methods=['GET', 'POST'])
@login_required
def adicionar_troca_oleo():
    try:
        colheitadeiras = Colheitadeira.query.all()
        
        if request.method == 'POST':
            colheitadeira_id = request.form['colheitadeira_id']
            data = datetime.datetime.strptime(request.form['data'], '%Y-%m-%d')
            horimetro = request.form['horimetro']
            tipo_oleo = request.form['tipo_oleo']
            quantidade = request.form['quantidade']
            observacoes = request.form['observacoes']
            
            troca = TrocaOleo(
                colheitadeira_id=colheitadeira_id,
                data=data,
                horimetro=horimetro,
                tipo_oleo=tipo_oleo,
                quantidade=quantidade,
                observacoes=observacoes
            )
            
            db.session.add(troca)
            db.session.commit()
            
            flash('Troca de óleo registrada com sucesso!')
            return redirect(url_for('listar_trocas_oleo'))
        
        return render_template('trocas_oleo/adicionar.html', colheitadeiras=colheitadeiras)
    except Exception as e:
        logger.error(f"Erro ao adicionar troca de óleo: {str(e)}")
        return render_template('error.html', error=str(e))

# Rotas para Registros de Horímetro
@app.route('/registros-horimetro')
@login_required
def listar_registros_horimetro():
    try:
        registros = RegistroHorimetro.query.order_by(RegistroHorimetro.data.desc()).all()
        return render_template('registros_horimetro/listar.html', registros=registros)
    except Exception as e:
        logger.error(f"Erro ao listar registros de horímetro: {str(e)}")
        return render_template('error.html', error=str(e))

@app.route('/registros-horimetro/adicionar', methods=['GET', 'POST'])
@login_required
def adicionar_registro_horimetro():
    try:
        colheitadeiras = Colheitadeira.query.all()
        
        if request.method == 'POST':
            colheitadeira_id = request.form['colheitadeira_id']
            data = datetime.datetime.strptime(request.form['data'], '%Y-%m-%d')
            valor = request.form['valor']
            horas_motor = request.form['horas_motor']
            observacoes = request.form['observacoes']
            
            registro = RegistroHorimetro(
                colheitadeira_id=colheitadeira_id,
                data=data,
                valor=valor,
                horas_motor=horas_motor,
                observacoes=observacoes
            )
            
            db.session.add(registro)
            db.session.commit()
            
            flash('Registro de horímetro adicionado com sucesso!')
            return redirect(url_for('listar_registros_horimetro'))
        
        return render_template('registros_horimetro/adicionar.html', colheitadeiras=colheitadeiras)
    except Exception as e:
        logger.error(f"Erro ao adicionar registro de horímetro: {str(e)}")
        return render_template('error.html', error=str(e))

# Rotas para Estoque
@app.route('/estoque')
@login_required
def listar_estoque():
    try:
        itens = ItemEstoque.query.all()
        return render_template('estoque/listar.html', itens=itens)
    except Exception as e:
        logger.error(f"Erro ao listar estoque: {str(e)}")
        return render_template('error.html', error=str(e))

@app.route('/estoque/adicionar', methods=['GET', 'POST'])
@login_required
def adicionar_item_estoque():
    try:
        if request.method == 'POST':
            codigo = request.form['codigo']
            nome = request.form['nome']
            categoria = request.form['categoria']
            quantidade = request.form['quantidade']
            unidade = request.form['unidade']
            valor_unitario = request.form['valor_unitario']
            estoque_minimo = request.form['estoque_minimo']
            localizacao = request.form.get('localizacao', '')
            fornecedor = request.form.get('fornecedor', '')
            data_ultima_compra = request.form.get('data_ultima_compra', '')
            if data_ultima_compra:
                data_ultima_compra = datetime.datetime.strptime(data_ultima_compra, '%Y-%m-%d')
            descricao = request.form.get('descricao', '')
            observacoes = request.form.get('observacoes', '')
            
            item = ItemEstoque(
                codigo=codigo,
                nome=nome,
                categoria=categoria,
                quantidade=quantidade,
                unidade=unidade,
                valor_unitario=valor_unitario,
                estoque_minimo=estoque_minimo,
                localizacao=localizacao,
                fornecedor=fornecedor,
                data_ultima_compra=data_ultima_compra,
                descricao=descricao,
                observacoes=observacoes
            )
            
            db.session.add(item)
            db.session.commit()
            
            # Registrar movimentação de entrada inicial
            movimentacao = MovimentacaoEstoque(
                item_id=item.id,
                tipo='Entrada',
                quantidade=quantidade,
                data=datetime.datetime.now(),
                responsavel=current_user.nome,
                observacao='Cadastro inicial do item'
            )
            
            db.session.add(movimentacao)
            db.session.commit()
            
            flash('Item adicionado ao estoque com sucesso!')
            return redirect(url_for('listar_estoque'))
        
        return render_template('estoque/adicionar.html')
    except Exception as e:
        logger.error(f"Erro ao adicionar item ao estoque: {str(e)}")
        return render_template('error.html', error=str(e))

@app.route('/estoque/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_item_estoque(id):
    try:
        item = ItemEstoque.query.get_or_404(id)
        
        if request.method == 'POST':
            item.codigo = request.form['codigo']
            item.nome = request.form['nome']
            item.categoria = request.form['categoria']
            item.unidade = request.form['unidade']
            item.valor_unitario = request.form['valor_unitario']
            item.estoque_minimo = request.form['estoque_minimo']
            item.localizacao = request.form.get('localizacao', '')
            item.fornecedor = request.form.get('fornecedor', '')
            data_ultima_compra = request.form.get('data_ultima_compra', '')
            if data_ultima_compra:
                item.data_ultima_compra = datetime.datetime.strptime(data_ultima_compra, '%Y-%m-%d')
            item.descricao = request.form.get('descricao', '')
            item.observacoes = request.form.get('observacoes', '')
            
            db.session.commit()
            flash('Item atualizado com sucesso!')
            return redirect(url_for('listar_estoque'))
        
        return render_template('estoque/editar.html', item=item)
    except Exception as e:
        logger.error(f"Erro ao editar item do estoque: {str(e)}")
        return render_template('error.html', error=str(e))

@app.route('/estoque/visualizar/<int:id>')
@login_required
def visualizar_item_estoque(id):
    try:
        item = ItemEstoque.query.get_or_404(id)
        movimentacoes = MovimentacaoEstoque.query.filter_by(item_id=id).order_by(MovimentacaoEstoque.data.desc()).all()
        
        return render_template('estoque/visualizar.html', item=item, movimentacoes=movimentacoes)
    except Exception as e:
        logger.error(f"Erro ao visualizar item do estoque: {str(e)}")
        return render_template('error.html', error=str(e))

@app.route('/estoque/movimentacao', methods=['GET', 'POST'])
@login_required
def registrar_movimentacao_estoque():
    try:
        itens = ItemEstoque.query.all()
        
        if request.method == 'POST':
            item_id = request.form['item_id']
            tipo = request.form['tipo']
            quantidade = float(request.form['quantidade'])
            data = datetime.datetime.strptime(request.form['data'], '%Y-%m-%d')
            responsavel = current_user.nome
            observacao = request.form.get('observacao', '')
            
            # Atualizar quantidade do item
            item = ItemEstoque.query.get(item_id)
            if tipo == 'Entrada':
                item.quantidade = float(item.quantidade) + quantidade
            else:  # Saída
                if float(item.quantidade) < quantidade:
                    flash('Quantidade insuficiente em estoque!')
                    return redirect(url_for('registrar_movimentacao_estoque'))
                item.quantidade = float(item.quantidade) - quantidade
            
            # Registrar movimentação
            movimentacao = MovimentacaoEstoque(
                item_id=item_id,
                tipo=tipo,
                quantidade=quantidade,
                data=data,
                responsavel=responsavel,
                observacao=observacao
            )
            
            db.session.add(movimentacao)
            db.session.commit()
            
            flash('Movimentação registrada com sucesso!')
            return redirect(url_for('listar_estoque'))
        
        return render_template('estoque/movimentacao.html', itens=itens)
    except Exception as e:
        logger.error(f"Erro ao registrar movimentação de estoque: {str(e)}")
        return render_template('error.html', error=str(e))

@app.route('/estoque/relatorio')
@login_required
def relatorio_estoque():
    try:
        itens = ItemEstoque.query.all()
        itens_abaixo_minimo = [item for item in itens if float(item.quantidade) < float(item.estoque_minimo)]
        
        valor_total_estoque = sum(float(item.quantidade) * float(item.valor_unitario) for item in itens)
        
        return render_template('estoque/relatorio.html', 
                              itens=itens, 
                              itens_abaixo_minimo=itens_abaixo_minimo,
                              valor_total_estoque=valor_total_estoque)
    except Exception as e:
        logger.error(f"Erro ao gerar relatório de estoque: {str(e)}")
        return render_template('error.html', error=str(e))

# Rota para relatórios
@app.route('/relatorios')
@login_required
def relatorios():
    try:
        return render_template('relatorios.html')
    except Exception as e:
        logger.error(f"Erro na rota de relatórios: {str(e)}")
        return render_template('error.html', error=str(e))

# Página de erro
@app.errorhandler(404)
def page_not_found(e):
    return render_template('error.html', error="Página não encontrada"), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('error.html', error=str(e)), 500

# Adicione o template de erro
with app.app_context():
    try:
        os.makedirs(os.path.join(app.root_path, 'templates'), exist_ok=True)
        error_template_path = os.path.join(app.root_path, 'templates', 'error.html')
        if not os.path.exists(error_template_path):
            with open(error_template_path, 'w') as f:
                f.write("""
<!DOCTYPE html>
<html>
<head>
    <title>Erro - Sistema de Manutenção</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
    <link rel="stylesheet" href="{{ url_for('static', filename='css/john-deere-theme.css') }}">
</head>
<body>
    <div class="container">
        <div class="error-container">
            <h1>Ocorreu um erro</h1>
            <p>{{ error }}</p>
            <p>Por favor, entre em contato com o administrador do sistema.</p>
            <a href="{{ url_for('login') }}" class="btn btn-primary">Voltar para o login</a>
        </div>
    </div>
</body>
</html>
                """)
    except Exception as e:
        logger.error(f"Erro ao criar template de erro: {str(e)}")

if __name__ == '__main__':
    # Definir porta para o Render.com
    port = int(os.environ.get('PORT', 8000))
    app.run(debug=True, host='0.0.0.0', port=port)
