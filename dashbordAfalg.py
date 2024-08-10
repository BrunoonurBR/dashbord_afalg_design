pip install dash plotly pandas psycopg2-binary sqlalchemy

import dash
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import plotly.express as px
from dash.dependencies import Input, Output
from sqlalchemy import create_engine

# Configuração da conexão com o banco de dados PostgreSQL
DATABASE_URL = "postgresql://usuario:senha@localhost:5432/nome_do_banco"
engine = create_engine(DATABASE_URL)

# Consulta SQL para obter os dados financeiros
query = "SELECT data, receitas, despesas FROM dados_financeiros"
df = pd.read_sql(query, engine)

# Calcula o lucro
df['lucros'] = df['receitas'] - df['despesas']

# Inicialização do aplicativo Dash
app = dash.Dash(__name__)
app.title = "Dashboard Financeiro"

# Layout do dashboard
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content')
], style={'fontFamily': 'Arial, sans-serif', 'padding': '20px'})

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
    dcc.Graph(id='graph', style={'height': '70vh'})
], style={'maxWidth': '1000px', 'margin': 'auto'})

# Callback para atualizar o gráfico com base na seleção do dropdown
@app.callback(
    Output('graph', 'figure'),
    [Input('dropdown', 'value')]
)
def update_graph(selected_column):
    fig = px.line(df, x='data', y=selected_column, title=f'{selected_column.capitalize()} ao longo do tempo')
    fig.update_layout(margin={'l': 20, 'r': 20, 't': 40, 'b': 20})
    return fig

# Callback para atualizar o conteúdo da página com base na URL
@app.callback(
    Output('page-content', 'children'),
    [Input('url', 'pathname')]
)
def display_page(pathname):
    if (pathname == '/dashboard'):
        return dashboard_page
    else:
        return index_page

# Executa o servidor
if __name__ == '__main__':
    app.run_server(debug=True)

