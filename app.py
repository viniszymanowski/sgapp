from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
import os
from datetime import datetime
from functools import wraps

app = Flask(__name__)
app.secret_key = 'sistema_manutencao_secret_key'

# Configuração do banco de dados
DATABASE = 'sistema_manutencao.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# Inicializar o banco de dados
def init_db():
    # Verificar se o banco de dados já existe
    if not os.path.exists(DATABASE):
        # Importar e executar o script de inicialização
        import init_db
        init_db.init_db()

# Função decoradora para verificar se o usuário está logado
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Por favor, faça login para acessar esta página.', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Rotas
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM usuarios WHERE username = ? AND password = ?',
                          (username, password)).fetchone()
        conn.close()
        
        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['nome'] = user['nome']
            session['tipo'] = user['tipo']
            flash(f'Bem-vindo, {user["nome"]}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Usuário ou senha inválidos.', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Você saiu do sistema.', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    conn = get_db_connection()
    
    # Contagem de colheitadeiras
    total_colheitadeiras = conn.execute('SELECT COUNT(*) as count FROM colheitadeiras').fetchone()['count']
    
    # Colheitadeiras operacionais
    colheitadeiras_operacionais = conn.execute('SELECT COUNT(*) as count FROM colheitadeiras WHERE status = "Operacional"').fetchone()['count']
    
    # Manutenções pendentes
    manutencoes_pendentes = conn.execute('SELECT COUNT(*) as count FROM manutencoes_preventivas WHERE status = "Pendente"').fetchone()['count']
    
    # Manutenções corretivas abertas
    manutencoes_corretivas = conn.execute('SELECT COUNT(*) as count FROM manutencoes_corretivas WHERE status != "Concluída"').fetchone()['count']
    
    # Itens com estoque baixo
    itens_estoque_baixo = conn.execute('SELECT COUNT(*) as count FROM estoque WHERE quantidade <= estoque_minimo').fetchone()['count']
    
    # Próximas manutenções
    proximas_manutencoes = conn.execute('''
        SELECT mp.id, mp.descricao, mp.data_agendada, c.modelo, c.numero_serie
        FROM manutencoes_preventivas mp
        JOIN colheitadeiras c ON mp.colheitadeira_id = c.id
        WHERE mp.status = "Pendente"
        ORDER BY mp.data_agendada
        LIMIT 5
    ''').fetchall()
    
    # Últimas trocas de óleo
    ultimas_trocas = conn.execute('''
        SELECT to.id, to.data, to.horimetro, to.proxima_troca, c.modelo, c.numero_serie, c.horimetro_atual
        FROM trocas_oleo to
        JOIN colheitadeiras c ON to.colheitadeira_id = c.id
        ORDER BY to.data DESC
        LIMIT 5
    ''').fetchall()
    
    conn.close()
    
    return render_template('dashboard.html', 
                          total_colheitadeiras=total_colheitadeiras,
                          colheitadeiras_operacionais=colheitadeiras_operacionais,
                          manutencoes_pendentes=manutencoes_pendentes,
                          manutencoes_corretivas=manutencoes_corretivas,
                          itens_estoque_baixo=itens_estoque_baixo,
                          proximas_manutencoes=proximas_manutencoes,
                          ultimas_trocas=ultimas_trocas)

@app.route('/colheitadeiras')
@login_required
def colheitadeiras():
    conn = get_db_connection()
    colheitadeiras = conn.execute('SELECT * FROM colheitadeiras ORDER BY modelo').fetchall()
    conn.close()
    return render_template('colheitadeiras.html', colheitadeiras=colheitadeiras)

@app.route('/colheitadeira/<int:id>')
@login_required
def colheitadeira_detalhes(id):
    conn = get_db_connection()
    colheitadeira = conn.execute('SELECT * FROM colheitadeiras WHERE id = ?', (id,)).fetchone()
    
    # Manutenções preventivas
    manutencoes_preventivas = conn.execute('''
        SELECT * FROM manutencoes_preventivas 
        WHERE colheitadeira_id = ? 
        ORDER BY data_agendada DESC
    ''', (id,)).fetchall()
    
    # Manutenções corretivas
    manutencoes_corretivas = conn.execute('''
        SELECT * FROM manutencoes_corretivas 
        WHERE colheitadeira_id = ? 
        ORDER BY data_abertura DESC
    ''', (id,)).fetchall()
    
    # Trocas de óleo
    trocas_oleo = conn.execute('''
        SELECT * FROM trocas_oleo 
        WHERE colheitadeira_id = ? 
        ORDER BY data DESC
    ''', (id,)).fetchall()
    
    # Registros de horímetro
    registros_horimetro = conn.execute('''
        SELECT * FROM registros_horimetro 
        WHERE colheitadeira_id = ? 
        ORDER BY data DESC
    ''', (id,)).fetchall()
    
    conn.close()
    
    if colheitadeira is None:
        flash('Colheitadeira não encontrada.', 'danger')
        return redirect(url_for('colheitadeiras'))
    
    return render_template('colheitadeira_detalhes.html', 
                          colheitadeira=colheitadeira,
                          manutencoes_preventivas=manutencoes_preventivas,
                          manutencoes_corretivas=manutencoes_corretivas,
                          trocas_oleo=trocas_oleo,
                          registros_horimetro=registros_horimetro)

@app.route('/manutencoes_preventivas')
@login_required
def manutencoes_preventivas():
    conn = get_db_connection()
    manutencoes = conn.execute('''
        SELECT mp.*, c.modelo, c.numero_serie 
        FROM manutencoes_preventivas mp
        JOIN colheitadeiras c ON mp.colheitadeira_id = c.id
        ORDER BY mp.data_agendada
    ''').fetchall()
    conn.close()
    return render_template('manutencoes_preventivas.html', manutencoes=manutencoes)

@app.route('/manutencoes_corretivas')
@login_required
def manutencoes_corretivas():
    conn = get_db_connection()
    manutencoes = conn.execute('''
        SELECT mc.*, c.modelo, c.numero_serie 
        FROM manutencoes_corretivas mc
        JOIN colheitadeiras c ON mc.colheitadeira_id = c.id
        ORDER BY mc.data_abertura DESC
    ''').fetchall()
    conn.close()
    return render_template('manutencoes_corretivas.html', manutencoes=manutencoes)

@app.route('/trocas_oleo')
@login_required
def trocas_oleo():
    conn = get_db_connection()
    trocas = conn.execute('''
        SELECT to.*, c.modelo, c.numero_serie, c.horimetro_atual
        FROM trocas_oleo to
        JOIN colheitadeiras c ON to.colheitadeira_id = c.id
        ORDER BY to.data DESC
    ''').fetchall()
    conn.close()
    return render_template('trocas_oleo.html', trocas=trocas)

@app.route('/horimetro')
@login_required
def horimetro():
    conn = get_db_connection()
    registros = conn.execute('''
        SELECT rh.*, c.modelo, c.numero_serie
        FROM registros_horimetro rh
        JOIN colheitadeiras c ON rh.colheitadeira_id = c.id
        ORDER BY rh.data DESC
    ''').fetchall()
    
    colheitadeiras = conn.execute('SELECT id, modelo, numero_serie FROM colheitadeiras ORDER BY modelo').fetchall()
    
    conn.close()
    return render_template('horimetro.html', registros=registros, colheitadeiras=colheitadeiras)

@app.route('/estoque')
@login_required
def estoque():
    conn = get_db_connection()
    itens = conn.execute('SELECT * FROM estoque ORDER BY categoria, nome').fetchall()
    conn.close()
    return render_template('estoque.html', itens=itens)

# Inicializar o banco de dados antes de iniciar o servidor
init_db()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
