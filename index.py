from dash import Dash, html, dcc
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate
from dash.dependencies import Input, Output

# Connect to main app.py file
from app import app
from app import server

# Connect to your app pages
from apps import home, grafo_y_pred, consultas, consultas_grafo

navbar = dbc.NavbarSimple(
    children=[
        dbc.NavItem(dbc.NavLink("Grafo y Predicción", href="/apps/grafo_y_pred")),
        dbc.DropdownMenu(
            children=[
                dbc.DropdownMenuItem("Descriptivas", id = 'cons-desc', href="/apps/consultas", disabled = True),
                dbc.DropdownMenuItem("Grafo Interactivo", id = 'cons-grafo', href="/apps/consultas_grafo", disabled = True),
            ],
            nav=True,
            in_navbar=True,
            label="Consultas",
        ),
    ],
    brand="BD UNAM",
    brand_href="/apps/home",
    color="primary",
    dark=True,
)


app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    navbar,
    html.Br(),
    html.Div(id='page-content', children=[]),
    # Almacenamiento de datos
    dcc.Store(id='output-data-upload'),  # DataFrame original
    dcc.Store(id='sample_train'),        # DataFrame de train
    dcc.Store(id='sample_test'),         # DataFrame de test
    dcc.Store(id='nodes_catalogue'),     # DataFrame de los node catalogue
    dcc.Store(id='graphCompleto'),       # Grafo completo
    dcc.Store(id='graphSubCompleto'),    # Sub grafo completo
    dcc.Store(id='graphTrain'),          # Grafo de train
    dcc.Store(id='graphTrainSub'),       # Grafo de train - sub
    dcc.Store(id='graphTest'),           # Grafo de test
    dcc.Store(id='graphTestSub'),        # Grafo de test - sub
    dcc.Store(id='subGraphAutArt'),      # Sub Grafo Autor Articulo 
    dcc.Store(id='matrizTFIDF-global'),
    dcc.Store(id='BiGrams-list'),
    dcc.Store(id='modelos_fechas'),
])

#____________Callbacks_______
#__________Mostrar layout correspondiente_________
@app.callback(Output('page-content', 'children'),
              [Input('url', 'pathname')])
def display_page(pathname):
    if pathname == '/apps/grafo_y_pred':
        return grafo_y_pred.layout
    if pathname == '/apps/consultas':
        return consultas.layout
    if pathname == '/apps/consultas_grafo':
        return consultas_grafo.layout
    return home.layout

#__________Mostrar layout correspondiente_________
@app.callback(Output('cons-desc', 'disabled'),
              Output('cons-grafo', 'disabled'),
              Input('output-data-upload', 'data'),
              prevent_initial_call = True)
def activate_refs(data):
    if data is not None:
        return False, False


if __name__ == '__main__':
    #app.run_server(debug=False, host='0.0.0.0', port=8000)
    #app.run_server(debug=True, host='0.0.0.0', port=8000)
    app.run(debug=False)

