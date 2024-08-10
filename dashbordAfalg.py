pip install dash plotly pandas psycopg2-binary sqlalchemy flask flask-login werkzeug


import dash
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import plotly.express as px
from dash.dependencies import Input, Output, State
from sqlalchemy import create_engine, text
from flask import Flask, redirect, url_for
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import io

# Configuração da conexão com o banco de dados PostgreSQL
DATABASE_URL = "postgresql://USER_BANCO:senha@localhost:5432/NOME_DO_BANCO"
engine = create_engine(DATABASE_URL)

# Consulta SQL para obter os dados financeiros
query = "SELECT data, receitas, despesas FROM dados_financeiros"
df = pd.read_sql(query, engine)

# Calcula o lucro
df['lucros'] = df['receitas'] - df['despesas']

# Inicialização do aplicativo Flask e Dash
server = Flask(__name__)
server.secret_key = 'chave_secreta'
app = dash.Dash(__name__, server=server)
app.title = "Dashboard Financeiro"

# Configuração do Flask-Login
login_manager = LoginManager()
login_manager.init_app(server)
login_manager.login_view = 'login'

# Modelo de usuário
class User(UserMixin):
    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password = password

# Usuários de exemplo (em um cenário real, você buscaria do banco de dados)
users = {'admin': User(id=1, username='USER_BANCO', password=generate_password_hash('SENHA_BANCO'))}

@login_manager.user_loader
def load_user(user_id):
    return users.get('admin')

# Layout do dashboard
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content')
], style={'fontFamily': 'Arial, sans-serif', 'padding': '20px'})

# Layout da página de login
login_page = html.Div([
    html.H2("Login"),
    dcc.Input(id='username', type='text', placeholder='Usuário', style={'margin': '10px'}),
    dcc.Input(id='password', type='password', placeholder='Senha', style={'margin': '10px'}),
    html.Button('Login', id='login-button', n_clicks=0),
    html.Div(id='login-output')
], style={'textAlign': 'center', 'maxWidth': '300px', 'margin': 'auto'})

# Layout da página inicial
index_page = html.Div([
    html.H1("Dashboard Financeiro", style={'textAlign': 'center'}),
    html.Div([
        html.H2("Visão Geral"),
        html.P(f"Total de Receitas: R$ {df['receitas'].sum():,.2f}"),
        html.P(f"Total de Despesas: R$ {df['despesas'].sum():,.2f}"),
        html.P(f"Total de Lucros: R$ {df['lucros'].sum():,.2f}"),
    ], style={'padding': '20px', 'backgroundColor': '#f9f9f9', 'borderRadius': '5px', 'maxWidth': '600px', 'margin': 'auto'}),
    html.Hr(),
    dcc.Link('Ir para o Dashboard', href='/dashboard', style={'display': 'block', 'textAlign': 'center', 'margin': '20px 0'})
])

# Layout do dashboard financeiro
dashboard_page = html.Div([
    html.H1("Dashboard Financeiro", style={'textAlign': 'center'}),
    dcc.Link('Voltar para a Página Inicial', href='/', style={'display': 'block', 'textAlign': 'center', 'margin': '20px 0'}),
    dcc.DatePickerRange(
        id='date-picker-range',
        start_date=df['data'].min(),
        end_date=df['data'].max(),
        display_format='YYYY-MM-DD',
        style={'margin': 'auto', 'display': 'block'}
    ),
    dcc.Dropdown(
        id='dropdown',
        options=[
            {'label': 'Receitas', 'value': 'receitas'},
            {'label': 'Despesas', 'value': 'despesas'},
            {'label': 'Lucros', 'value': 'lucros'}
        ],
        value='receitas',
        style={'maxWidth': '300px', 'margin': 'auto'}
    ),
    dcc.Graph(id='line-graph', style={'height': '70vh'}),
    dcc.Graph(id='bar-graph', style={'height': '70vh'}),
    html.Hr(),
    html.H2("Inserir/Atualizar Dados", style={'textAlign': 'center'}),
    dcc.Input(id='input-data', type='date', placeholder='Data', style={'margin': '10px'}),
    dcc.Input(id='input-receitas', type='number', placeholder='Receitas', style={'margin': '10px'}),
    dcc.Input(id='input-despesas', type='number', placeholder='Despesas', style={'margin': '10px'}),
    html.Button('Inserir/Atualizar', id='insert-update-button', n_clicks=0, style={'display': 'block', 'margin': '20px auto'}),
    html.Div(id='insert-update-output'),
    html.Hr(),
    html.H2("Deletar Dados", style={'textAlign': 'center'}),
    dcc.Input(id='delete-data', type='date', placeholder='Data', style={'margin': '10px'}),
    html.Button('Deletar', id='delete-button', n_clicks=0, style={'display': 'block', 'margin': '20px auto'}),
    html.Div(id='delete-output'),
    html.Hr(),
    html.Button('Exportar Dados', id='export-button', n_clicks=0, style={'display': 'block', 'margin': '20px auto'}),
    dcc.Download(id='download-dataframe-csv')
], style={'maxWidth': '1000px', 'margin': 'auto'})

# Callback para atualizar os gráficos com base na seleção do dropdown e no intervalo de datas
@app.callback(
    [Output('line-graph', 'figure'), Output('bar-graph', 'figure')],
    [Input('dropdown', 'value'), Input('date-picker-range', 'start_date'), Input('date-picker-range', 'end_date')]
)
@login_required
def update_graphs(selected_column, start_date, end_date):
    filtered_df = df[(df['data'] >= start_date) & (df['data'] <= end_date)]
    line_fig = px.line(filtered_df, x='data', y=selected_column, title=f'{selected_column.capitalize()} ao longo do tempo')
    bar_fig = px.bar(filtered_df, x='data', y=selected_column, title=f'Comparação de {selected_column.capitalize()}')
    line_fig.update_layout(margin={'l': 20, 'r': 20, 't': 40, 'b': 20})
    bar_fig.update_layout(margin={'l': 20, 'r': 20, 't': 40, 'b': 20})
    return line_fig, bar_fig

# Callback para inserir ou atualizar dados
@app.callback(
    Output('insert-update-output', 'children'),
    [Input('insert-update-button', 'n_clicks')],
    [State('input-data', 'value'), State('input-receitas', 'value'), State('input-despesas', 'value')]
)
@login_required
def insert_update_data(n_clicks, data, receitas, despesas):
    if n_clicks > 0 and data and receitas is not None and despesas is not None:
        with engine.connect() as conn:
            query = text("""
                INSERT INTO dados_financeiros (data, receitas, despesas)
                VALUES (:data, :receitas, :despesas)
                ON CONFLICT (data) DO UPDATE
                SET receitas = EXCLUDED.receitas,
                    despesas = EXCLUDED.despesas
            """)
            conn.execute(query, data=data, receitas=receitas, despesas=despesas)
        return html.Div('Dados inseridos/atualizados com sucesso!', style={'color': 'green'})
    return html.Div()

# Callback para deletar dados
@app.callback(
    Output('delete-output', 'children'),
    [Input('delete-button', 'n_clicks')],
    [State('delete-data', 'value')]
)
@login_required
def delete_data(n_clicks, data):
    if n_clicks > 0 and data:
        with engine.connect() as conn:
            query = text("DELETE FROM dados_financeiros WHERE data = :data")
            conn.execute(query, data=data)
        return html.Div('Dados deletados com sucesso!', style={'color': 'green'})
    return html.Div()

# Callback para atualizar o conteúdo da página com base na URL
@app.callback(
    Output('page-content', 'children'),
    [Input('url', 'pathname')]
)
def display_page(pathname):
    if pathname == '/dashboard':
        if current_user.is_authenticated:
            return dashboard_page
        else:
            return redirect(url_for('login'))
    elif pathname == '/login':
        return login_page
    else:
        return index_page

# Callback para processar o login
    @app.callback(
    Output('login-output', 'children'),
    [Input('login-button', 'n_clicks')],
    [State('username', 'value'), State('password', 'value')]
)
    def login(n_clicks, username, password):
     if n_clicks > 0:
        user = users.get(username)
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            return html.Div('Usuário ou senha incorretos', style={'color': 'red'})

# Callback para exportar os dados para CSV
    @app.callback(
    Output('download-dataframe-csv', 'data'),
    [Input('export-button', 'n_clicks')],
    prevent_initial_call=True
)
    def export_data(n_clicks):
        if n_clicks > 0:
         buffer = io.StringIO()
        df.to_csv(buffer, index=False)
        buffer.seek(0)
        return dcc.send_data_frame(buffer.getvalue(), "dados_financeiros.csv")

# Executa o servidor
    if __name__ == '__main__':
        app.run_server(debug=True)