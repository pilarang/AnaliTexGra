from dash import Dash, html, dash_table, dcc, callback, Output, Input, State
import dash_bootstrap_components as dbc
import dash_cytoscape as cyto
import pandas as pd
import networkx as nx
import numpy as np
import base64, io
import json
import contextlib

from apps import consultas_functions as cf

from app import app

nombres_areas = {'TC': 'Teoría de la Computación',
                    'ISBD': 'Ingeniería de Software y Bases de Datos',
                    'SIAV': 'Señales, Imágenes y Ambientes Virtuales',
                    'IA': 'Inteligencia Artificial',
                    'RS': 'Redes y Seguridad en Cómputo'}

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
        if G.nodes[nodo]['tipo'] == 'keyword':
            list_keywords.append(nodo)
    return list_autores, list_articulos, list_afiliaciones, list_keywords

def getNodesSubgraph(G, elementos, opcion):
    nodos = []
    if opcion == '1':
        for nodo in elementos:      #elementos son autores
            articulos = list(cf.getNodesQuery(G, 'articulo', nodo))
            coautores = []
            for articulo in articulos:
                coautores.extend(list(cf.getNodesQuery(G, 'autor', articulo)))
            coautores = list(np.unique(coautores)) 
            nodos.extend(articulos)
            nodos.extend(coautores)
    elif opcion == '2' or opcion == '3':
        for nodo in elementos:    #elementos son keywords o afiliaciones
            nodos.extend(G.neighbors(nodo))
        nodos.extend(elementos)
    elif opcion == '4':
        for nodo in G.nodes():
            if G.nodes[nodo]['tipo'] == 'articulo':
                if G.nodes[nodo]['Area'] in elementos:
                    nodos.append(nodo)
                    nodos.extend(list(cf.getNodesQuery(G, 'autor', nodo)))
    elif opcion == '5':
        for nodo in G.nodes():
            if G.nodes[nodo]['tipo'] == 'articulo':
                if G.nodes[nodo]['Year'] in elementos:
                    nodos.append(nodo)
                    nodos.extend(list(cf.getNodesQuery(G, 'autor', nodo)))

    return list(np.unique(nodos))


def createSubGraph(cyInt, elementos, opcion):
    G = convertCYToGraph(cyInt)
    # Filtrar solo elementos seleccionados
    elementos = list(map(str, elementos))
    nodos = getNodesSubgraph(G, elementos, opcion)
    
    # Asignar colores
    G_sub = G.subgraph(nodos).copy()

    cy = nx.readwrite.json_graph.cytoscape_data(G_sub)
    
    for i in cy['elements']['nodes']:
        nodo = i['data']['name']
        tipo = G.nodes[nodo]['tipo']
        if tipo == 'articulo':
            i.update({'style': {'background-color': '#FF0000'}})
        elif tipo == 'autor':
            i.update({'style': {'background-color': '#0000FF'}})
            if nodo in elementos:
                i.update({'style': {'background-color': '#87CEEB'}})
        elif tipo == 'keyword':
            i.update({'style': {'background-color': '#4CBB17'}})
        elif tipo == 'afiliacion':
            i.update({'style': {'background-color': '#FFD900'}})
        else:
            i.update({'style': {'background-color': '#0F0000'}})

        if nodo in elementos:
            i['data']['label'] = nodo
        else:
            i['data']['label'] = ''

    return cy['elements']


layout = [html.Div([
    html.H2('Consultas con Grafo Interactivo'),
    ], style = {
            'textAlign': 'justify',
            'padding-top':'20px', 
            'padding-left':'40px', 
            'padding-right':'40px', 
            'padding-bottom':'40px'}),
    
    html.Div([
        html.H4('Elige el tipo de subgrafo'),
        html.Br(),
        html.P('''En esta parte es posible obtener un grafo más pequeño con información sobre autores, afiliaciones,
            artículos y keywords.'''),
        dbc.Row([
            dbc.Col(
                dbc.InputGroup([
                    dbc.InputGroupText("Subgrafo por: "),
                    dbc.Select(options=[
                        {"label": "Autor y coautores", "value": 1},
                        {"label": "Keywords y artículos", "value": 2},
                        {"label": "Afiliación y autores", "value": 3},
                        {"label": "Área de conocimiento de artículos", "value": 4},
                        {"label": "Año de publicación de artículos", "value": 5},
                        ], id = 'dropdown-subgrafo'),
                    ]), width = 5),
            dbc.Col(
                dbc.Row([
                    dbc.Col(
                        dbc.InputGroupText("Nodos: "), width = 2),
                    dbc.Col(html.Div(id='children-nodos-subgrafo'), width = 10)])),
            dbc.Col(dbc.Button("Crear", id="button-subgrafo", n_clicks=0, disabled=True), width = 1, style = {'textAlign': 'right'}),
            ]),
        html.Br(),
        dbc.Row([
            dbc.Col(cyto.Cytoscape(
                        id='cytoscape-consultas-subgrafo',
                        minZoom = 0.25,
                        maxZoom = 6,
                        layout={'name': 'cose'},
                        style={'width': '100%', 'height': '600px', 'background-color': '#EEEEEE'}), width = 8),
            dbc.Col(html.Div(id = 'cytoscape-tapNodeData-json-consultas'), width = 4),
            ])
        ], style = {
            'textAlign': 'justify',
            'padding-top':'20px', 
            'padding-left':'40px', 
            'padding-right':'40px', 
            'padding-bottom':'40px'}),
    ]

#___________Callbacks_________
#____________ Habilitar botón Subgrafos __________
@app.callback(Output('button-subgrafo','disabled'),
              Input('dropdown-nodos-subgrafo', 'value'))
def activate_button_buscar(value):
    if value == None:
        return True

#____________ Opciones tercer dropdown: Buscar __________
@app.callback(Output('children-nodos-subgrafo', 'children'),
              Input('dropdown-subgrafo', 'value'),
              Input('graphCompleto', 'data'),
              Input('output-data-upload', 'data'),
              prevent_initial_call = True)
def update_opciones_buscar(value, cy_G, jsonified_cleaned_data):
    if cy_G is not None:
        G = convertCYToGraph(cy_G)
        df = pd.read_json(jsonified_cleaned_data, orient='split')
        list_autores, list_articulos, list_afiliaciones, list_keywords = getCatalogues(G)
        list_years = list(df['Año'].unique())
        list_areas = list(df['Area'].unique())
        options = []
        
        if value == '1':
            options = list_autores
        elif value == '2':
            options = list_keywords
        elif value == '3':
             options = list_afiliaciones
        elif value == '4':
            for area in list_areas:
                if area in list(nombres_areas.keys()):
                    options.append(area + ' - ' + nombres_areas[area])
        elif value == '5':
            options = list_years
  
        return dcc.Dropdown(options, multi=True, id='dropdown-nodos-subgrafo')

#____________ Mostrar subgrafo __________
@app.callback(Output('cytoscape-consultas-subgrafo', 'elements'),
              Input('button-subgrafo','n_clicks'),
              Input('graphCompleto', 'data'),
              State('dropdown-subgrafo','value'),
              State('dropdown-nodos-subgrafo','value'),
              prevent_initial_call = True)
def consultas_frec(n_clicks, cy_G, opcion, elementos):
    if cy_G is not None and n_clicks > 0:
        if opcion == '4':      
            elementos_area = []
            for elemento in elementos:
                if elemento.split('-')[0].strip() in nombres_areas.keys():
                    elementos_area.append(elemento.split('-')[0].strip())
                else:
                    elementos_area.append(elemento)
            return createSubGraph(cy_G, elementos_area, opcion)  
        return createSubGraph(cy_G, elementos, opcion)

# ___________ Mostrar atributos de un nodo
@callback(Output('cytoscape-tapNodeData-json-consultas', 'children'),
          Input('cytoscape-consultas-subgrafo', 'tapNodeData'),
          prevent_initial_call = True)
def displayTapNodeData(data):
    if dict(data)['tipo'] == 'autor':
        return dbc.Card([
            dbc.CardHeader(html.H5(dict(data)['value']))
            ], color = 'info', outline = True)
    elif dict(data)['tipo'] == 'articulo':
        ModalBody = [
            html.Div([html.H4(key), html.P(value)])
            for key, value in dict(data).items()
            if key not in ['value', 'id', 'name', 'tipo', 'Abstract','label']
            ]
        with contextlib.suppress(Exception):
            abstract = dict(data)['Abstract']
            ModalBody.append(html.Div([html.H4('Abstract'), html.P(abstract)]))
        return html.Div([
            dbc.Modal([
                dbc.ModalHeader(dbc.ModalTitle(dict(data)['value']), close_button=False),
                dbc.ModalBody(ModalBody),
                dbc.ModalFooter(
                    dbc.Button("Close", id="close-backdrop-cg", className="ms-auto", n_clicks=0))
                ],
                id="modal-atributos-articulo-cg",
                scrollable=True,
                is_open=False),
            dbc.Card([
                dbc.CardHeader(html.H5(dict(data)['value'])),
                dbc.CardBody([
                    dbc.Button("Abrir detalles", id="open-details-cg", n_clicks=0, color='success', outline=True),
                    ])
                ], color = 'danger', outline = True),
            ])
    elif dict(data)['tipo'] == 'keyword':
        return dbc.Card([
            dbc.CardHeader(html.H5(dict(data)['value']))
            ], color = 'success', outline = True)
    elif dict(data)['tipo'] == 'afiliacion':
        return dbc.Card([
            dbc.CardHeader(html.H5(dict(data)['value']))
            ], color = 'warning', outline = True)

# ___________ Abrir/cerrar modal de los detalles de un artículo
@app.callback(Output("modal-atributos-articulo-cg", "is_open"),
             [Input("open-details-cg", "n_clicks"), Input("close-backdrop-cg", "n_clicks")],
             State("modal-atributos-articulo-cg", "is_open"),
             prevent_initial_call = True)
def toggle_modal(n1, n2, is_open):
    return not is_open if n1 or n2 else is_open

# ___________ Abrir/cerrar modal de la lista de artículos
@app.callback(Output("modal-lista-articulo-cg", "is_open"),
             [Input("close-lista-cg", "n_clicks"), Input("open-articles-cg", "n_clicks")],
             State("modal-lista-articulo-cg", "is_open"),
             prevent_initial_call = True)
def toggle_modal(n1, n2, is_open):
    return not is_open if n1 or n2 else is_open
