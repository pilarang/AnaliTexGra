from dash import Dash, html, dash_table, dcc, callback, Output, Input, State
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
import dash_cytoscape as cyto
import pandas as pd
import networkx as nx
import numpy as np
import base64, io
import json
from apps import consultas_functions as cf
from apps import text_functions as textf

from app import app

def convertCYToGraph(cy):
    """Función que transforma un Cytoscape JSON y devuelve un grafo G de NetworkX"""
    G = nx.Graph()
    for list_nodo in cy['elements']['nodes']:
        nodo = dict(list_nodo['data'])
        G.add_node(nodo['value'])
        for atributo, valor in nodo.items():
            if atributo in ['id', 'name', 'value']:
                continue
            G.nodes[nodo['value']][atributo] = valor
    for list_edges in cy['elements']['edges']:
        edge = dict(list_edges['data'])
        G.add_edge(edge['source'], edge['target'])
    return G

def getCatalogues(G):
    list_autores = []
    list_articulos = []
    list_afiliaciones = []
    list_keywords = []
    for nodo in G.nodes():
        if G.nodes[nodo]['tipo'] == 'autor':
            list_autores.append(nodo)
        if G.nodes[nodo]['tipo'] == 'articulo':
            list_articulos.append(nodo)
        if G.nodes[nodo]['tipo'] == 'afiliacion':
            list_afiliaciones.append(nodo)
    return list_autores, list_articulos, list_afiliaciones

layout = [html.Div([
    html.H2('Consultas Descriptivas'),
    ], style = {
            'textAlign': 'justify',
            'padding-top':'20px', 
            'padding-left':'40px', 
            'padding-right':'40px', 
            'padding-bottom':'40px'}),
    
    html.Div([
        html.H4('Buscar por Autor, Artículo, Keyword o Afiliación'),
        html.Br(),
        html.P('''En esta sección es posible buscar información sobre autores de un artículo, autores de una afiliación, 
            artículos que contienen una keyword, artículos de un autor, keywords de un artículo y afiliaciones de un 
            autor.'''),
        dbc.Row([
            dbc.Col([
                dbc.InputGroup([
                    dbc.InputGroupText("Buscar"),
                    dbc.Select(options=[
                        {"label": "Autor", "value": 'autor'},
                        {"label": "Artículo", "value": 'articulo'},
                        {"label": "Afiliación", "value": 'afiliacion'},
                        {"label": "Keyword", "value": 'keyword'},
                        ], id = 'dropdown-buscar-tipo'),
                    ]),
                ],width = 3),
            dbc.Col([
                dbc.InputGroup([
                    dbc.InputGroupText("Por"),
                    html.Div(id='children-buscar-por'),
                    ]),
                ],width = 2),
            dbc.Col([
                html.Div(id='children-buscar'),
                ], width = 6),
            dbc.Col([
                dbc.Button("Buscar", id="button-buscar", n_clicks=0, disabled=True),
                ], width = 1, style = {'textAlign': 'right'})

            ]),
        html.Br(),
        html.Div(id='resultados-busqueda'),
        ], style = {
            'textAlign': 'justify',
            'padding-top':'20px', 
            'padding-left':'40px', 
            'padding-right':'40px', 
            'padding-bottom':'40px'}),
    
    html.Div([
        html.H4('Consultas por Frecuencia'),
        html.Br(),
        html.P('''Para estas consultas es posible conocer cuales son los autores, artículos, afiliaciones, etc. que
            tienen la mayor cantidad de elementos. Por ejemplo: ¿qué artículo tiene más autores?'''),
        dbc.Row([
            dbc.Col(
                dbc.InputGroup([
                    dbc.InputGroupText("Preguntas: "),
                    dbc.Select(options=[
                        {"label": "¿Cuáles son las keywords más utilizadas?", "value": 1},
                        {"label": "¿Qué área de conocimiento tiene más artículos?", "value": 2},
                        {"label": "¿Qué autor tiene más colaboradores?", "value": 3},
                        {"label": "¿Qué afiliación tiene a los autores más productivos?", "value": 4},
                        {"label": "¿Qué artículo tiene más autores?", "value": 5},
                        ], id = 'dropdown-consultas-frec'),
                    ]), width = 11),
            dbc.Col(dbc.Button("Buscar", id="button-consultas-frec", n_clicks=0, disabled=True), width = 1, style = {'textAlign': 'right'}),
            ]),
        html.Br(),
        html.Div(id='resultados-consultas-frec'),
        ], style = {
            'textAlign': 'justify',
            'padding-top':'20px', 
            'padding-left':'40px', 
            'padding-right':'40px', 
            'padding-bottom':'40px'}),

    html.Div([
        html.H4('Similitud entre Artículos'),
        html.Br(),
        html.P('''Dado dos artículos, se muestra la similitud entre ambos. La similitud se representa como un porcentaje 
            de 0 al 100%, donde 100% siginifica que los artículos son iguales y 0% que no existe ninguna similitud.'''),
        dbc.Row([
            dbc.Col(
                dbc.InputGroup([
                    dbc.InputGroupText("Artículo 1 "),
                    dbc.Select(options = [], id = 'dropdown-similitud-art1'),
                    ]), width = 4),
            dbc.Col(
                dbc.InputGroup([
                    dbc.InputGroupText("Artículo 2 "),
                    dbc.Select(options = [], id = 'dropdown-similitud-art2'),
                    ]), width = 4),
            dbc.Col(
                dbc.InputGroup([
                    dbc.InputGroupText("En base a "),
                    dbc.Select(options = [
                        {"label": "Keywords", "value": 1},
                        {"label": "Abstract", "value": 2}
                        ], id = 'Similitud-basada-en')
                    ]), width = 2),
            dbc.Col(
                dbc.Button("Comparar artículos", id="button-similitud", n_clicks=0, disabled=True, style = {'textAlign': 'justify'}), 
                width = 2, style = {'textAlign': 'right'}),
            ]),
        html.Br(),
        html.Div(id='resultados-similitud'),
        ], style = {
            'textAlign': 'justify',
            'padding-top':'20px', 
            'padding-left':'40px', 
            'padding-right':'40px', 
            'padding-bottom':'40px'}),

    html.Div([
        html.H4('Buscar entre artículos'),
        html.Br(),
        html.P('¿Tiene alguna pregunta la cual desea responder a través de un artículo?'),
        html.P('''¡Puede hacerlo! Busque entre todos los artículos de la base de dato algún tema en específico. 
            El sistema le recomendará los 5 mejores artículos que pueden resolver su enigma, ordenados de mayor a 
            menor compatibilidad con su pregunta. '''),
        html.P('Nota: Procure usar términos técnicos para ofrecer una mejor calidad en los resultados'),
        html.Div(id = 'boton-inicial-para-TF-IDF'), # Mostrar advertencia para crear matriz/mostrar cuadro de entrada a pregunta
        dbc.Spinner(html.Div(id='resultados-busqueda-tecnica'))
        ], style = {
            'textAlign': 'justify',
            'padding-top':'20px', 
            'padding-left':'40px', 
            'padding-right':'40px', 
            'padding-bottom':'40px'})
    ]


#____________ Callbacks __________
#____________ Opciones segundo dropdown: Buscar por __________
@app.callback(Output('children-buscar-por', 'children'),
              Input('dropdown-buscar-tipo', 'value'))
def update_opciones_buscar_por(nodeType):
    if nodeType is None:
        options = []
    if nodeType == 'autor':
        options = [{"label": "Afiliación", "value": 'afiliacion'},{"label": "Artículo", "value": 'articulo'}]
    if nodeType == 'articulo':
        options = [{"label": "Keyword", "value": 'keyword'},{"label": "Autor", "value": 'autor'}]
    if nodeType == 'afiliacion':
        options = [{"label": "Autor", "value": 'autor'}]
    if nodeType == 'keyword':
        options = [{"label": "Artículo", "value": 'articulo'}]
    return dbc.Select(options=options, id = 'dropdown-buscar-por')

#____________ Opciones tercer dropdown: Buscar __________
@app.callback(Output('children-buscar', 'children'),
              Input('dropdown-buscar-por', 'value'),
              Input('graphCompleto', 'data'))
def update_opciones_buscar(nodeType, cy_G):
    if cy_G is not None:
        G = convertCYToGraph(cy_G)
        list_autores, list_articulos, list_afiliaciones = getCatalogues(G)
        if nodeType is None:
            options = [] 
        if nodeType == 'autor':
            options = [{'label':x, 'value':x} for x in list_autores]
        if nodeType == 'articulo':
            options = [{'label':x, 'value':x} for x in list_articulos]
        if nodeType == 'afiliacion':
            options = [{'label':x, 'value':x} for x in list_afiliaciones]
        if nodeType == 'keyword':
            return dbc.Input(type='text', id='dropdown-buscar')
        return dbc.Select(options=options, id='dropdown-buscar')

#____________ Habilitar botón Buscar __________
@app.callback(Output('button-buscar','disabled'),
              Input('dropdown-buscar', 'value'))
def activate_button_buscar(value):
    if value == None:
        return True

#____________ Mostrar resultados de búsqueda __________
@app.callback(Output('resultados-busqueda', 'children'),
              Input('graphCompleto', 'data'),
              Input('button-buscar', 'n_clicks'),
              State('dropdown-buscar-tipo', 'value'),
              State('dropdown-buscar-por', 'value'),
              State('dropdown-buscar', 'value'))
def buscar(cy_G, nBuscar, nodeType, buscarPor, atribute):
    if nodeType is None or buscarPor is None or atribute is None or cy_G is None:
        return dbc.Alert('Faltan datos para hacer la consulta', color = 'danger')
    else:
        G = convertCYToGraph(cy_G)
        list_nodes = cf.getNodesQuery(G, nodeType, atribute)
        
        if nodeType == 'autor':
            html_layout = [html.P(['Los ', html.Span('autores', style = {'font-weight': 'bold'}), ' encontrados para ',
                html.Span(atribute, style = {'font-weight': 'bold'}), ' son: '])]
            for element in list_nodes:
                html_layout.append(html.Li(element))

        if nodeType == 'articulo':
            html_layout = [html.P(['Los ', html.Span('artículos', style = {'font-weight': 'bold'}), ' encontrados para ',
                html.Span(atribute, style = {'font-weight': 'bold'}), ' son: '])]
            for element in list_nodes:
                info = cf.getInfoArticle(G, element)
                html_layout.append(html.Li(element))
                #for item in info.items():
                #    if item[0] == 'keywords':
                #        html_layout.append(html.P(item[0]))
                #        for x in item[1]:
                #            html_layout.append(html.P(x))
                #    else:
                #        html_layout.append(html.P(item[0] + ' ' + item[1]))

        if nodeType == 'afiliacion':
            html_layout = [html.P(['Las ', html.Span('afiliaciones', style = {'font-weight': 'bold'}), ' encontradas para ',
                html.Span(atribute, style = {'font-weight': 'bold'}), ' son: '])]
            for element in list_nodes:
                html_layout.append(html.Li(element))

        if nodeType == 'keyword':
            html_layout = [html.P(['Las ', html.Span('keywords', style = {'font-weight': 'bold'}), ' encontradas para ',
                html.Span(atribute, style = {'font-weight': 'bold'}), ' son: '])]
            for element in list_nodes:
                html_layout.append(html.Li(element))

        return dbc.Card(dbc.CardBody(html_layout))

#____________ Habilitar botón Buscar __________
@app.callback(Output('button-consultas-frec','disabled'),
              Input('dropdown-consultas-frec', 'value'))
def activate_button_buscar(value):
    if value == None:
        return True

#____________ Mostrar resultados de consulta de frecuencia __________
@app.callback(Output('resultados-consultas-frec', 'children'),
              Input('graphCompleto', 'data'),
              Input('graphSubCompleto', 'data'),
              Input('button-consultas-frec', 'n_clicks'),
              State('dropdown-consultas-frec','value'))
def consultas_frec(cy_G, cy_G_sub, nConsultas, value):
    if cy_G is not None and cy_G_sub is not None and value is not None:
        G = convertCYToGraph(cy_G)
        G_sub = convertCYToGraph(cy_G_sub)
        html_layout = []
        i = 0

        if value == '1':
            res = cf.keywordFrecuency(G)
        if value == '2':
            res = cf.areaFrecuency(G)
        if value == '3':
            res = cf.coAuthors(G_sub)
        if value == '4':
            res = cf.dependenciaFrecuency(G)
        if value == '5':
            res = cf.articuloAutorFrecuency(G)

        for item in res.items():
            if i == 5:
                break
            html_layout.append(html.Li(item[0] +': ' +str(item[1])))
            i += 1
        return dbc.Card(dbc.CardBody(html_layout))   

#____________ Opciones dropdown para Similitud __________
@app.callback(Output('dropdown-similitud-art1','options'),
              Output('dropdown-similitud-art2','options'),
              Input('graphCompleto', 'data'))
def opciones_similitud(cy_G):
    if cy_G is not None:
        G = convertCYToGraph(cy_G)
        list_autores, list_articulos, list_afiliaciones = getCatalogues(G)
        options = [{'label':x, 'value':x} for x in list_articulos] 
        return options, options 

#____________ Obtener similitud
@app.callback(Output('resultados-similitud', 'children'),
              Input('button-similitud', 'n_clicks'),
              State('graphCompleto', 'data'),
              State('Similitud-basada-en', 'value'),
              State('dropdown-similitud-art1', 'value'),
              State('dropdown-similitud-art2', 'value'))
def getSimilitud(n, cy_graph, parametro, art1, art2):
    if n > 0:
        G = convertCYToGraph(cy_graph)
        similitud = 0
        final = ''
        if parametro == '1':   # Keywords
            similitud = textf.similitudArticulosByKeywords(G, art1, art2)
            if similitud == -1:
                return dbc.Alert('Uno o ambos artículos carecen de Keywords, por lo que no es posible obtener la similitud entre ellos', color="warning")
            final = 'en base a las Keywords de ambos artículos'
        else:                # Abstract
            similitud = textf.similitudArticulosByAbstract(G, art1, art2)
            if similitud == -1:
                return dbc.Alert('Uno o ambos artículos carecen de Abstract, por lo que no es posible obtener la similitud entre ellos', color="warning")
            final = 'en base a los abstracts'
        return dbc.Card(
            dbc.CardBody([
                html.P(['Los artículos ',
                       html.Li(art1),
                       html.Li(art2),
                       ' son un ', html.Span(f'{str(similitud * 100)}%', style = {'font-weight': 'bold'}), ' similares entre si, ', final])
                ]))

#____________ Habilitar botón Similitud __________
@app.callback(Output('button-similitud','disabled'),
              Input('Similitud-basada-en', 'value'))
def activate_button_buscar(value):
    if value is None:
        return True

#____________ Mostrar entre crear matriz o buscar directamente
@app.callback(Output('boton-inicial-para-TF-IDF', 'children'),
              Input('matrizTFIDF-global', 'data'))
def showCreateMatriz_search(df):
    if df is None:
        return [dbc.Row([
            dbc.Col(width=2),
            dbc.Col([
                dbc.Alert('Antes de comenzar necesita generar la matriz TF/IDF. Para ello, comience dando click en \'Generar matriz TF/IDF\'', color = 'warning')
                ], width=6),
            dbc.Col([
                dbc.Button('Generar matriz TF/IDF', n_clicks=0, id = 'Crear-matrizTFIDF')
                ], width=2)
            ]),
        dbc.Progress([
            dbc.Progress(value=0, id='progressMatriz-1', bar=True, color='secondary', animated=True, style={"height": "30px"}),
            dbc.Progress(value=0, id='progressMatriz-2', bar=True, color='secondary', animated=True, style={"height": "30px"}),
            dbc.Progress(value=0, id='progressMatriz-3', bar=True, color='secondary', animated=True, style={"height": "30px"})]
            , style={"height": "30px"})
        ]
    return [dbc.InputGroup([
            dbc.Input(placeholder = 'Buscar entre artículos', id='search-in-articles-text'),
            dbc.Button('Buscar', id = 'search-in-articles', n_clicks=0)
            ])
        ]

# _____________ Bloquear boton de generar matriz
@app.callback(Output('Crear-matrizTFIDF', 'disabled'),
              Output('progressMatriz-1', 'value'),
              Output('progressMatriz-1', 'label'),
              Input('Crear-matrizTFIDF', 'n_clicks'),
              State('matrizTFIDF-global', 'data'))
def disableBoton(n, matriz):
    if n > 0 and matriz is None:
        return True, 15, 'Generando corpus y biGrams...'
    raise PreventUpdate

# _____________ Obtener corpus y biGrams
@app.callback(Output('BiGrams-list', 'data'),
              Output('progressMatriz-2', 'value'),
              Output('progressMatriz-2', 'label'),
              Input('Crear-matrizTFIDF', 'n_clicks'),
              State('output-data-upload', 'data'))
def createCorpusAndBiGrams(n, df_json):
    if n > 0:
        df = pd.read_json(df_json, orient='split')
        texto = textf.createCorpus(df)
        return textf.foundBiGrams(texto), 45, 'Obteniendo matriz TF/IDF...'
    raise PreventUpdate

# _____________ Obtener matriz TF/IDF
@app.callback(Output('matrizTFIDF-global', 'data'),
              Output('progressMatriz-3', 'value'),
              Output('progressMatriz-3', 'label'),
              Input('BiGrams-list', 'data'),
              State('graphCompleto', 'data'))
def createMatriz(BiGrams, graph_cy):
    if BiGrams is not None:
        G = convertCYToGraph(graph_cy)
        df = textf.createGlobalMatriz(G, BiGrams)
        return df.to_json(date_format='iso', orient='split'), 40, 'Completado'
    raise PreventUpdate

# _____________ Realizar búsqueda
@app.callback(Output('resultados-busqueda-tecnica', 'children'),
              Input('search-in-articles', 'n_clicks'),
              State('search-in-articles-text', 'value'),
              State('BiGrams-list', 'data'),
              State('matrizTFIDF-global', 'data'))
def searchInArticles(n, pregunta, biGrams, matrizTFIDF_JSON):
    if pregunta is not None and n > 0:
        matriz = pd.read_json(matrizTFIDF_JSON, orient='split')
        respuesta = textf.answerQuestion(matriz, pregunta, biGrams)
        final_response = [
            html.Li([titulo, '--- similitud: ', rows['similitud'].round(2)])
            for titulo, rows in respuesta.iterrows()
        ]
        return [dbc.Card([
            dbc.CardBody([
                html.P('Los siguientes artículos son recomendados: '),
                html.Div(final_response)])
                ])
            ]