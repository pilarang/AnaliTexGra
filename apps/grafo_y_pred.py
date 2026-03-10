from dash import Dash, html, dash_table, dcc, callback, Output, Input, State, no_update
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
import dash_cytoscape as cyto
import pandas as pd
import networkx as nx
import base64, io
import sys
import contextlib
import json
import joblib
from datetime import datetime

from apps import hassan as hs
from apps import modelos as models
from apps import text_functions as textf

from app import app


#importar csv de github
#url = 'https://raw.githubusercontent.com/FrancisBL5/PaginaWeb/main/web/datasets/UNAM_Completo_Corregido.csv'
#df_original = pd.read_csv(url,index_col=0)

#importar csv de la carpeta datasets
sys.path.append('../')
#df_original = pd.read_csv('datasets/UNAM_Completo_Corregido.csv')
df_original = pd.read_csv(r'C:\Users\pilarang\0-ProyAcademicosGrafo-Integrado\3-AplicacionWebDash\datasets\UNAM_Completo_Corregido.csv')

buffer_array = []
buffer = io.BytesIO()

def convertGraphToCY(G):
    """Función que transforma un grafo de NetworkX en un Cytoscape JSON format"""
    cy = nx.readwrite.json_graph.cytoscape_data(G)
    for i in cy['elements']['nodes']:
        nodo = i['data']['name']
        try:
            tipo = G.nodes[nodo]['tipo']
            if tipo == 'articulo':
                i.update({'style': {'background-color': '#FF0000'}})
            elif tipo == 'autor':
                i.update({'style': {'background-color': '#0000FF'}})
            elif tipo == 'keyword':
                i.update({'style': {'background-color': '#00FF00'}})
            elif tipo == 'afiliacion':
                i.update({'style': {'background-color': '#FFFF00'}})
            else:
                i.update({'style': {'background-color': '#0F0000'}})
            return cy
        except Exception as e:
            i.update({'style': {'background-color': '#0000FF'}})
    return cy

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

def createSubGraphArtAut(cyInt):
    """Función que recibe un Mapping de cytoscape, genera un grafo a partir de él, para posteriormente
    generar un subgrafo que contiene únicamente autores y artículos. Este subgrafo es convertido a JSON
    para poder ser almacenado"""
    G = convertCYToGraph(cyInt)
    # Filtrar solo autores y artículos
    nodosArtAut = [
        nodo
        for nodo in list(G.nodes())
        if G.nodes[nodo]['tipo'] not in ['keyword', 'afiliacion']
    ]
    # Asignar colores
    G_sub = G.subgraph(nodosArtAut).copy()
    pos = nx.spring_layout(G_sub)
    cy = nx.readwrite.json_graph.cytoscape_data(G_sub)
    for i in cy['elements']['nodes']:
        nodo = i['data']['name']
        i.update({'position': {'x': pos[nodo][0]*6*G_sub.number_of_nodes(), 'y': pos[nodo][1]*6*G_sub.number_of_nodes()}})
        tipo = G.nodes[nodo]['tipo']
        if tipo == 'articulo':
            i.update({'style': {'background-color': '#FF0000'}})
        elif tipo == 'autor':
            i.update({'style': {'background-color': '#0000FF'}})
        else:
            i.update({'style': {'background-color': '#0F0000'}})
    return cy['elements']

def lookForArticles(autor1, autor2, G):
    """Función que obtiene una lista con los artículos en los cuales ambos autores han colaborado"""
    list_articles = []
    for articulo in G.neighbors(autor1):
        if G.nodes[articulo]['tipo'] == 'articulo':
            if articulo in G.neighbors(autor2):
                list_articles.append(articulo)
    return list_articles

def modalArticles(autor1, autor2, list_articles):
    """Función que obtiene una lista de artículos y lo muestra en un modal"""
    """contentList = [
        html.Ol(articulo)
        for articulo in list_articles
        ]"""
    ModalBody = [
        html.P(["Artículos en los cuales ",
            html.Span(autor1, style = {'font-weight': 'bold'}), " y ",
            html.Span(autor2, style = {'font-weight': 'bold'}), " han colaborado:"]),
        html.Div([
            html.Ul([
                html.Li(articulo)
                for articulo in list_articles
                ]),
            ])
        ]
    return html.Div([
        dbc.Modal([
            dbc.ModalHeader(dbc.ModalTitle("Lista de artículos")),
            dbc.ModalBody(ModalBody),
            dbc.ModalFooter(
                dbc.Button("Close", id="close-lista", className="ms-auto", n_clicks=0))
            ],
            id="modal-lista-articulo",
            scrollable=True,
            is_open=False),
        dbc.Alert('Los autores ya han colaborado anteriormente', color="success"),
        dbc.Button("Ver artículos", id="open-articles", n_clicks=0, color='success', outline=True)
        ])

def resultLinkPrediction(lista_resultados):
    """Función que, en base a los resultados, define si dos autores pueden o no colaborar en un futuro"""
    contador = {}
    for elem in lista_resultados:
        contador[elem] = contador.get(elem, 0) + 1
    for key, value in contador.items():
        if value > 3:
            if key == 0:
                return dbc.Alert('No es probable que los autores colaboren en un futuro', color = 'danger')
            elif key == 1:
                return dbc.Alert('Es posible que los autores si colaboren en un futuro', color = 'success')
        # Valor de la RBF - Network
        if key not in [0, 1]:
            if key > 0.6:
                return dbc.Alert('Es posible que los autores si colaboren en un futuro', color = 'success')
            elif key < 0.4:
                return dbc.Alert('No es probable que los autores colaboren en un futuro', color = 'danger')
            else:
                return dbc.Alert('No se tiene la suficiente certeza para poder decir si los autores pueden o no colaborar en un futuro', color = 'warning')

layout = [html.Div([
    html.H2('Carga de Datos'),
    html.Br(),
    dbc.Label('Elige una opción:'),
    dbc.RadioItems(options=[
        {'label':'Utilizar Base de Datos de la UNAM', 'value':1},
        {'label':'Utilizar Base de Datos propia', 'value':2},
        ], value=1, persistence = True, persistence_type = 'session', inline = True, id='radioitems-bd'),
    html.Br(),
    html.Div(id = 'carga-datos'),
    html.Div(id = 'alerta'),
    #dcc.Interval(id="progress-interval", n_intervals=0, interval=400, disabled=False),
    #html.H4('Barra de progreso'),
    #dbc.Progress(id="progress", value = 0, label = "", color='secondary', animated=True, style={"height": "30px"}),
    html.Div([
        dbc.Progress([
            dbc.Progress(value=0, id='progress-1', bar=True, color='secondary', style={"height": "30px"}),
            dbc.Progress(value=0, id='progress-2', bar=True, color='secondary', style={"height": "30px"}),
            dbc.Progress(value=0, id='progress-3', bar=True, color='secondary', style={"height": "30px"}),
            dbc.Progress(value=0, id='progress-4', bar=True, color='secondary', style={"height": "30px"}),
            dbc.Progress(value=0, id='progress-5', bar=True, color='secondary', style={"height": "30px"})
            ], style={"height": "30px"}),
        ], id='general-progress')
    ], style = {
            'textAlign': 'justify',
            'padding-top':'20px', 
            'padding-left':'40px', 
            'padding-right':'40px', 
            'padding-bottom':'40px'}),

    html.Div([
        html.H2('Generación de Grafo'),
        html.P(['En el siguiente recuadro se mostrará el grafo interactivo donde los nodos ',
            html.Span('Autores', style = {'color':'blue'}), ' se mostrarán en ',
            html.Span('azul', style = {'color':'blue'}), ' y los nodos ',
            html.Span('Artículo', style = {'color':'red'}), ' se mostrarán en ',
            html.Span('rojo', style = {'color':'red'}), '''. Al hacer clic en ellos se mostrará su nombre en el 
                recuadro debajo del grafo. También es posible alejar y acercar el grafo.''']),
        html.P('''Espere unos segundos a que cargue el grafo. En el caso de estar usando la Base de Datos UNAM, 
            la espera será de aproximadamente 10 segundos.'''),
        html.Br(),
        dbc.Row([
            dbc.Col([
                html.H4('Grafo Completo', style={'textAlign': 'center'}),
                cyto.Cytoscape(
                    id='cytoscape-event-callbacks_GraphComplete',
                    minZoom = 0.05,
                    maxZoom = 6,
                    layout={'name': 'preset'},
                    style={'width': '100%', 'height': '600px', 'background-color': '#EEEEEE'}),
                html.Br(),
                html.Div(id='cytoscape-tapNodeData-json'),
                ], width = 7),
            dbc.Col([
                html.H4('Link Prediction', style={'textAlign': 'center'}),
                html.P("""Ponga a prueba los modelos de Machine Learning y compruebe si un par de autores
                       pueden o no colaborar en un futuro."""),
                html.P("""Para comenzar, necesitará seleccionar dos autores. Seleccione un autor en el grafo interactivo
                       y si está conforme con esa elección, proceda a elegir al siguiente apoyándose de los Radio Items.
                       Para ejecutar los modelos, haga click en \"Predecir\""""),
                html.P('''Una vez que se muestren los resultados, si desea hacer otra predicción con otros autores, haga 
                        click en \"Hacer otra predicción\"'''),
                dbc.Card(
                    dbc.CardBody(id='autores-seleccionados', children=[
                        dbc.Row([
                            dbc.Col([
                                html.Br(),
                                dbc.RadioItems(
                                    id = 'editarAutoresRadioItems',
                                    options=[
                                        {"label": "Seleccionar Autor 1", "value": 1},
                                        {"label": "Seleccionar Autor 2", "value": 2}],
                                    labelCheckedClassName="text-success",
                                    inputCheckedClassName="border border-success bg-success",
                                    value = 1)
                                ], width=5),
                            dbc.Col([
                                dbc.ListGroup([
                                    dbc.ListGroupItem('Autor 1', id='autor1'),
                                    dbc.ListGroupItem('Autor 2', id='autor2'),
                                    ], flush=True)
                                ], width=7)
                            ]),
                        html.Br(),
                        dbc.Row([
                            dbc.Col(width=2),
                            dbc.Col([
                                dbc.Button('Predecir', id = 'buttonPredecir', color = 'success', outline = True, disabled=False, n_clicks=0),
                                ], width=3),
                            dbc.Col([
                                dbc.Button('Hacer otra predicción', id = 'buttonReiniciarPredecir', color = 'danger', outline = True, disabled=True, n_clicks=0),
                                ], width=5)
                            ]),
                        html.Br(),
                        html.Div(id = 'Res_LinkPrediction')
                        ]),
                    ),
                
                html.Br(),
                ], width = 5)
            ])
        ], style = {
            'textAlign': 'justify',
            'padding-top':'20px', 
            'padding-left':'40px', 
            'padding-right':'40px', 
            'padding-bottom':'40px'}),

    html.Div([
        html.H2('Validación de Modelos'),
        html.P('Las métricas que arrojan los modelos creados son:'),
        dbc.Row([
            dbc.Col([
                html.H4('Scores balanceados', style={'textAlign': 'center'}),
                html.Div(id = 'res_bal'),
                ], width=6),
            dbc.Col([
                html.H4('Scores positivos', style={'textAlign': 'center'}),
                html.Div(id = 'res_pos'),
                ], width=6)
            ]),
        ], style = {
            'textAlign': 'justify',
            'padding-top':'20px', 
            'padding-left':'40px', 
            'padding-right':'40px', 
            'padding-bottom':'40px'})
    ]

#____________ Callbacks __________
#____________ Decisión BD
@app.callback(Output('carga-datos', 'children'),
              Output('alerta','children'),
              Input('radioitems-bd', 'value'))
def decide_bd(valor):
    print(valor)
    if valor == 2:
        return [html.P('Cargue el archivo .csv que contiene los datos.'),
                dcc.Upload(id='upload-data', children = html.Div([
                    'Drag and Drop or ',
                    html.A('Select Files')]), style={
                        'height': '60px',
                        'lineHeight': '60px',
                        'borderWidth': '3px',
                        'borderStyle': 'dashed',
                        'borderRadius': '10px',
                        'textAlign': 'center',
                        'margin': '10px'},
                    ),
                html.Br()], [html.Div(dbc.Alert([
                    html.H5("Advertencia", className="alert-heading"),
                    html.P('Primero es necesario cargar un archivo con extensión .csv')
                    ], color="danger"), id = 'message')]
    return [html.Div(dcc.Upload(id='upload-data'))],[html.Div(id='message')]

#____________ Recibir el archivo inicial
@app.callback(Output('output-data-upload', 'data'),
              Output('nodes_catalogue', 'data'),
              Output('message', 'children'),
              Output('progress-1', 'value'),
              Output('progress-1', 'label'),
              Input('radioitems-bd','value'),
              Input('upload-data', 'contents'),
              State('upload-data', 'filename'),
              prevent_initial_call = True)
def upload_datos(bd_option, list_of_contents, filename):
    #print('valor ' + str(bd_option))
    if bd_option == 2:
        if list_of_contents is not None and filename is not None:
            try:
                if '.csv' in filename:
                    content_type, content_string = list_of_contents.split(',')
                    decoded = base64.b64decode(content_string)
                    df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
                else:
                    return [], [], dbc.Alert([
                                html.H5("Advertencia", className="alert-heading"),
                                html.P('El archivo cargado no tiene extensión .csv'),
                                html.P('Inténtalo de nuevo')], color="danger"), no_update, no_update
            except Exception as e:
                print(e)
                return [],[],html.Div(dbc.Alert("Algo raro pasa aquí", color="danger")), no_update, no_update
            df_filter, nodes_catalogue = hs.filterAndSplit(df)      #Conservar solo autores filtrados y no toda la base
            return df_filter.to_json(date_format='iso', orient='split'), nodes_catalogue.to_json(date_format='iso', orient='split'), [], 15, 'Generando grafos...'
    else: 
        df_filter, nodes_catalogue = hs.filterAndSplit(df_original)      #Conservar solo autores filtrados y no toda la base
        return df_filter.to_json(date_format='iso', orient='split'), nodes_catalogue.to_json(date_format='iso', orient='split'), [], 15, 'Generando grafos...'
    raise PreventUpdate

#____________ Obtener grafos
@app.callback(Output('graphCompleto', 'data'),
              Output('graphSubCompleto', 'data'),
              Output('graphTrain', 'data'),
              Output('graphTrainSub', 'data'),
              Output('graphTest', 'data'),
              Output('graphTestSub', 'data'),
              Output('progress-2', 'value'),
              Output('progress-2', 'label'),
              Input('output-data-upload', 'data'),
              prevent_initial_call = True)
def getAllGraphs(jsonified_cleaned_data):
    if jsonified_cleaned_data is not None:
        df = pd.read_json(jsonified_cleaned_data, orient='split')
        G_completo, G_sub_completo, G_train, G_sub_train, G_test, G_sub_test = hs.createGraphs(df)
        cy_G_completo = convertGraphToCY(G_completo)
        cy_G_sub_completo = convertGraphToCY(G_sub_completo)
        cy_G_train = convertGraphToCY(G_train)
        cy_G_sub_train = convertGraphToCY(G_sub_train)
        cy_G_test = convertGraphToCY(G_test)
        cy_G_sub_test = convertGraphToCY(G_sub_test)
        return cy_G_completo, cy_G_sub_completo, cy_G_train, cy_G_sub_train, cy_G_test, cy_G_sub_test, 15, 'Generando samples...'

# ___________ Obtener grafo completo a dibujar
@app.callback(Output('subGraphAutArt', 'data'),
              Output('progress-5', 'value'),
              Output('progress-5', 'label'),
              Input('graphCompleto', 'data'),
              prevent_initial_call = True)
def getGraphCompleteAutArt(cy_graphComplete):
    if cy_graphComplete:
        return createSubGraphArtAut(cy_graphComplete), 25, 'Completado'
    raise PreventUpdate

# ___________ Dibujar grafo completo
@app.callback(Output('cytoscape-event-callbacks_GraphComplete', 'elements'),
              Input('subGraphAutArt', 'data'))
def drawGraphComplete(cy_graphAutArt):
    if cy_graphAutArt is not None:
        return cy_graphAutArt
    raise PreventUpdate

# ___________ Mostrar atributos de un nodo
@callback(Output('cytoscape-tapNodeData-json', 'children'),
          Input('cytoscape-event-callbacks_GraphComplete', 'tapNodeData'),
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
            if key not in ['value', 'id', 'name', 'tipo', 'Abstract']
            ]
        with contextlib.suppress(Exception):
            abstract = dict(data)['Abstract']
            ModalBody.append(html.Div([html.H4('TLR'), html.P(textf.textSummarization(abstract))]))
            ModalBody.append(html.Div([html.H4('Abstract'), html.P(abstract)]))
        return html.Div([
            dbc.Modal([
                dbc.ModalHeader(dbc.ModalTitle(dict(data)['value']), close_button=False),
                dbc.ModalBody(ModalBody),
                dbc.ModalFooter(
                    dbc.Button("Close", id="close-backdrop", className="ms-auto", n_clicks=0))
                ],
                id="modal-atributos-articulo",
                scrollable=True,
                is_open=False),
            dbc.Card([
                dbc.CardHeader(html.H5(dict(data)['value'])),
                dbc.CardBody([
                    dbc.Button("Abrir detalles", id="open-details", n_clicks=0, color='success', outline=True),
                    ])
                ], color = 'danger', outline = True),
            ])

# ___________ Abrir/cerrar modal de los detalles de un artículo
@app.callback(Output("modal-atributos-articulo", "is_open"),
             [Input("open-details", "n_clicks"), Input("close-backdrop", "n_clicks")],
             State("modal-atributos-articulo", "is_open"),
             prevent_initial_call = True)
def toggle_modal(n1, n2, is_open):
    return not is_open if n1 or n2 else is_open

# ___________ Abrir/cerrar modal de la lista de artículos
@app.callback(Output("modal-lista-articulo", "is_open"),
             [Input("close-lista", "n_clicks"), Input("open-articles", "n_clicks")],
             State("modal-lista-articulo", "is_open"),
             prevent_initial_call = True)
def toggle_modal(n1, n2, is_open):
    return not is_open if n1 or n2 else is_open

# ___________ Mostrar autores en listGroup
@app.callback(Output('autor1', 'children'),
              Output('autor2', 'children'),
              Input('cytoscape-event-callbacks_GraphComplete', 'tapNodeData'),
              State('editarAutoresRadioItems', 'value'),
              State('autor1', 'children'),
              State('autor2', 'children'),
              prevent_initial_call = True)
def showSelectedAutors(dataSel, opcion, textAutor1, textAutor2):
    if dict(dataSel)['tipo'] == 'autor':
        if opcion == 1:
            return dict(dataSel)['value'], textAutor2
        elif opcion == 2:
            return textAutor1, dict(dataSel)['value']
    return textAutor1, textAutor2

# ___________ Predecir y volver a predecir
@app.callback(Output('buttonPredecir', 'disabled'),
              Output('buttonReiniciarPredecir', 'disabled'),
              Output('Res_LinkPrediction', 'children'),
              Input('buttonPredecir', 'n_clicks'),
              Input('buttonReiniciarPredecir', 'n_clicks'),
              State('autor1', 'children'),
              State('autor2', 'children'),
              State('buttonPredecir', 'disabled'),
              State('buttonReiniciarPredecir', 'disabled'),
              State('graphCompleto', 'data'),
              State('graphSubCompleto', 'data'),
              State('sample_test', 'data'),
              State('modelos_fechas','data'),
              prevent_initial_call = True)
def predecir(nPredict, nRestart, Autor1, Autor2, deshabPredict, deshabRestar, cy_G, cy_G_sub, json_df_test, fechas):
    if nPredict > 0 and (Autor1 != 'Autor 1' and Autor2 != 'Autor 2') and deshabRestar == True:
        if Autor1 != Autor2:
            df_test = pd.read_json(json_df_test, orient='split')
            G = convertCYToGraph(cy_G)
            G_sub = convertCYToGraph(cy_G_sub)

            modelos = []       

            for i in range(6):
                
                #modelos.append(joblib.load('0-ProyAcademicosGrafo-Integrado/3-AplicacionWebDash/assets/modelos/modelo{}-{}.joblib'.format(i,fechas[i])))
                modelos.append(joblib.load('assets/modelos/modelo{}-{}.joblib'.format(i,fechas[i])))
                #modelos.append(joblib.load(buffer_array[i]))

            resultadosLinkPrediction = models.predecir(Autor1,Autor2, G, G_sub, df_test, modelos)
            if resultadosLinkPrediction == {} or resultadosLinkPrediction is None:
                listArticles = lookForArticles(Autor1, Autor2, G)
                return True, False, modalArticles(Autor1, Autor2, listArticles)
            mensajeAlerta = resultLinkPrediction(resultadosLinkPrediction['Respuesta'])
            resultadosLinkPrediction = pd.DataFrame(resultadosLinkPrediction)
            resultadosLinkPrediction = dbc.Table.from_dataframe(resultadosLinkPrediction, striped=True, bordered=True, hover=True)
            return True, False, [
                mensajeAlerta,
                dbc.Accordion([
                    dbc.AccordionItem(resultadosLinkPrediction, title = 'Expandir resultados para cada modelo')
                    ], start_collapsed=True)
                ]
        return False, True, dbc.Alert('Por favor, escoja dos autores diferentes entre sí', color="warning")
    elif nRestart > 0 and deshabPredict == True:
        return False, True, []

# ___________ Obtener samples
@app.callback(Output('sample_train', 'data'),
              Output('sample_test', 'data'),
              Output('progress-3', 'value'),
              Output('progress-3', 'label'),
              Input('graphTrain', 'data'),
              Input('graphTest', 'data'),
              Input('nodes_catalogue', 'data'),
              Input('graphTrainSub', 'data'),
              Input('graphTestSub', 'data'),
              prevent_initial_call = True)
def getSamples(cy_G_train, cy_G_test, nodes_catalogue_json, cy_G_sub_train, cy_G_sub_test):
    if cy_G_train is not None and cy_G_test is not None and cy_G_sub_train is not None and cy_G_sub_test is not None:
        G_train = convertCYToGraph(cy_G_train)
        G_test = convertCYToGraph(cy_G_test)
        G_sub_train = convertCYToGraph(cy_G_sub_train)
        G_sub_test = convertCYToGraph(cy_G_sub_test)
        nodes_catalogue = pd.read_json(nodes_catalogue_json, orient='split')
        print("Nodes catalogue listo")
        sample_train, sample_test = hs.createSamples(G_train, G_test, nodes_catalogue)
        print("Samples vacios")
        sample_train, sample_test = hs.getParameters(sample_train, sample_test, G_train, G_test, G_sub_train, G_sub_test)
        print("Samples llenos")
        return sample_train.to_json(date_format='iso', orient='split'), sample_test.to_json(date_format='iso', orient='split'), 30, 'Compilando modelos...'

# ___________ Obtener Metricas de los modelos
@app.callback(Output('res_bal', 'children'),
              Output('res_pos', 'children'),
              Output('modelos_fechas', 'data'),
              Output('progress-4', 'value'),
              Output('progress-4', 'label'),
              Input('sample_train', 'data'),
              Input('sample_test', 'data'))
def getMedidas(sample_train_json, sample_test_json):
    if sample_train_json is not None and sample_test_json is not None:
        df_sample_train = pd.read_json(sample_train_json, orient='split')
        df_sample_test = pd.read_json(sample_test_json, orient='split')
        modelos, res_bal, res_pos = models.transformVariables(df_sample_train, df_sample_test)
        res_bal = dbc.Table.from_dataframe(round(res_bal,3), striped=True, bordered=True, hover=True)
        res_pos = dbc.Table.from_dataframe(round(res_pos,3), striped=True, bordered=True, hover=True)

        fechas = []
        for i in range(6):
            now = datetime.now()
            str_fecha = '{}-{}-{}-{}-{}-{}'.format(now.year,now.month,now.day,now.hour,now.minute,now.second)
            joblib.dump(modelos[i], 'assets/modelos/modelo{}-{}.joblib'.format(str(i),str_fecha))
            fechas.append(str_fecha)
            #joblib.dump(modelos[i], buffer)
            #buffer_array.append(buffer)

        return res_bal,res_pos, fechas, 15, 'Dibujando grafo...'
    raise PreventUpdate

# Reiniciar barra
@app.callback(
    Output("general-progress", "children"),
    Input('progress-5', 'value'),
    prevent_initial_call = True)
def update_progress(progreso):
    if progreso is not None:
        dbc.Progress([
            dbc.Progress(value=0, id='progress-1', bar=True, color='secondary'),
            dbc.Progress(value=0, id='progress-2', bar=True, color='secondary'),
            dbc.Progress(value=0, id='progress-3', bar=True, color='secondary'),
            dbc.Progress(value=0, id='progress-4', bar=True, color='secondary'),
            dbc.Progress(value=0, id='progress-5', bar=True, color='secondary')
            ])
    raise PreventUpdate