import pandas as pd
import networkx as nx
from collections import defaultdict
import numpy as np

#Libreria creada para optimizar el codigo al momento de crear los grafos y subgrafos

def keywords_list(df):
    '''
    Obtención de todas las keywords de la base

    Parametros
    ---------
    df: dataframe de la base de datos

    Returns
    -------
    list_keywords: lista de keywords únicas

    '''
    list_keywords = []
    for index, row in df.iterrows():
        keywords = row['Keywords']
        if keywords != 0:                                               # Si existen keywords
            keywords_list = str(keywords).split(';')
            for keyword in keywords_list:
                if keyword != '':                                       # En ocasiones al usar split, se generan elementos de cadenas vacías
                    keyword = keyword.replace('.','')                   # Algunas keywords tienen caracteres de más
                    keyword = keyword.replace(':','')
                    keyword = keyword.lower()                           # Minúsculas
                    list_keywords.append(keyword.strip())
    # Lista de keywords únicas sin repetición
    list_keywords = np.unique(list_keywords)
    #print("Longitud lista Keywords únicas:", len(unique_keywords))

    return list_keywords


def createEdges_Key_Articles(G, titulo_val, keywords_val):
    '''
    Generación de aristas en un grafo entre un nodo artículo y los nodos de sus keywords

    Parametros
    ---------
    G: grafo a modificar
    titulo_val: str del titulo del artículo
    keywords_val: str de keywords de ese artículo separadas por ;

    Returns
    -------
    G: grafo modificado

    '''
    keywords_list = str(keywords_val).split(";")
    for keyword in keywords_list:
        if keyword != '':
            keyword = keyword.replace('.','')
            keyword = keyword.replace(':','')
            keyword = keyword.lower()
            keyword = keyword.strip()
            G.add_edge(titulo_val, keyword)                         # Arista entre artículo y keyword
    
    return G


def createArticulos(df, G):
    '''
    Creación de nodos Articulos con sus atributos en el grafo.

    Parametros
    ---------
    df: dataframe de la base de datos
    G: grafo a modificar

    Returns
    -------
    G: grafo modificado

    '''
    for index, row in df.iterrows():
        # Se almacenan todos los atributos de un artículo
        titulo_val = str(row['Titulo']).strip()
        Year_val = row['Año']
        ISBN_val = row['ISBN']
        ISSN_val = row['ISSN']
        Doi_val = row['Doi']
        Area_val = row['Area']
        URL_val = row['URL']
        keywords_val = row['Keywords']
        Abstract_val = row['Abstract']
        # Se genera el nodo del atículo correspondiente
        G.add_node(titulo_val, tipo = 'articulo')
        # Se comprueba la existencia de cada atributo, si existe, se guarda como atributo del nodo
        if Year_val != 0:
            G.nodes[titulo_val]['Year'] = str(int(Year_val))
        if ISBN_val != 0:
            G.nodes[titulo_val]['ISBN'] = ISBN_val
        if ISSN_val != 0:
            G.nodes[titulo_val]['ISSN'] = ISSN_val
        if Doi_val != 0:
            G.nodes[titulo_val]['Doi'] = Doi_val
        if Area_val != 0:
            G.nodes[titulo_val]['Area'] = Area_val
        if URL_val != 0:
            G.nodes[titulo_val]['URL'] = URL_val
        if Abstract_val != 0:
            G.nodes[titulo_val]['Abstract'] = Abstract_val
        if keywords_val != 0:
            G = createEdges_Key_Articles(G, titulo_val, keywords_val)

    return G


def dependencias_list(df_dependencias):
    '''
    Obtención de las dependencias en la base de datos.

    Parametros
    ---------
    df_dependencias: dataframe con las dependencias

    Returns
    -------
    list_dependencias: lista de dependencias

    '''
    list_dependencias = []
    for index, row in df_dependencias.iterrows():
        afiliacion1 = row['Afiliacion1']
        afiliacion2 = row['Afiliacion2']
        if afiliacion1 != 0:
            if afiliacion1 not in list_dependencias:
                list_dependencias.append(afiliacion1)
        if afiliacion2 != 0:
            if afiliacion2 not in list_dependencias:
                list_dependencias.append(afiliacion2)
    #print("Total dependencias: ", len(list_dependencias))

    return list_dependencias


def createEdges_Dep_Author(G, df):
    '''
    Generación de aristas en un grafo entre un nodo autor y los nodos de sus dependencias

    Parametros
    ---------
    G: grafo a modificar
    df: dataframe de la base de datos

    Returns
    -------
    G: grafo modificado

    '''
    for index, row in df.iterrows():
        autor = row['Autor_norm']
        autor = str(autor).strip()
        afiliacion1 = row['Afiliacion1']
        afiliacion2 = row['Afiliacion2']
        if afiliacion1 != 0:
            G.add_edge(autor,str(afiliacion1).strip())
        if afiliacion2 != 0:
            G.add_edge(autor,str(afiliacion2).strip())
    return G


def createGraph(dataframe):
    '''
    Creación del grafo con nodos de Autores, Keywords, Artículos y Dependencias y aristas
    autor-artículo, artículo-keyword, dependencia-autor.

    Parametros
    ---------
    dataframe: dataframe de la base de datos

    Returns
    -------
    G: grafo de la base de datos

    '''
    # --- Extraer keywords ----
    df = dataframe
    df_tit_key = df[['Titulo','Keywords']]
    df_tit_key = df_tit_key.drop_duplicates()
    df_tit_key = df_tit_key.fillna(0)

    # --- Generar lista de Keywords que se agregarán como nodos en el grafo
    unique_keywords = keywords_list(df_tit_key)

    # --- Agregar keywords como nodos al grafo
    G = nx.Graph()
    for keyword in unique_keywords:
        G.add_node(keyword, tipo = 'keyword')

    # --- Generar artículos y conexiones con las keywords
    df_articulos = df[['Titulo','Año','ISBN','ISSN','Doi','URL','Area','Keywords','Abstract']]
    df_articulos = df_articulos.drop_duplicates()
    df_articulos = df_articulos.fillna(0)

    G = createArticulos(df_articulos, G)

    # --- Autores ---
    df_tit_autor = df[['Titulo','Autor_norm']]
    df_tit_autor = df_tit_autor.fillna(0)
    #autores = df_tit_autor['Autor_norm'].to_list()

    #df_authors = df_tit_autor.groupby('Autor_norm',as_index=False).count()
    #df_authors = df_authors[df_authors['Titulo']>2]
    #df_authors = df_authors.reset_index(drop=True)
    #df_authors = df_authors[df_authors['Autor_norm'].isin(autores)]

    # --- Agregar autores ---
    for index, row in df_tit_autor.iterrows():
        autor = row['Autor_norm']
        autor = str(autor).strip()
        G.add_node(autor, tipo = 'autor')

    # --- Conectar autores con artículos
    for index, row in df_tit_autor.iterrows():
        autor = row['Autor_norm']
        autor = str(autor).strip()
        articulo = str(row['Titulo']).strip()
        G.add_edge(autor, articulo)

    # --- Afliaciones
    df_autor_afi = df[['Autor_norm','Afiliacion1','Afiliacion2']]
    df_autor_afi = df_autor_afi.fillna(0)               # Llena los espacios en blanco con 0´s
    df_autor_afi = df_autor_afi.drop_duplicates()

    # --- Agregar nodos de afiliaciones
    df_dependencias = df[['Afiliacion1','Afiliacion2']]
    df_dependencias = df_dependencias.fillna(0)               # Llena los espacios en blanco con 0´s
    df_dependencias = df_dependencias.drop_duplicates()

    list_dependencias = dependencias_list(df_dependencias)

    for dependencia in list_dependencias:
        G.add_node(str(dependencia).strip(), tipo = 'afiliacion')

    # --- Conectar dependencias con autores
    G = createEdges_Dep_Author(G, df_autor_afi)

    return G


def addAuthor(G_sub, df_authors):
    '''
    Creación y agregación de nodos autores con atributos de afiliaciones al grafo

    Parametros
    ---------
    G_sub : Grafo de NetworkX donde se agregarán nodos
    df_authors: dataframe con los datos de los autores

    Returns
    -------
    G_sub: grafo modificado

    '''
    for index, row in df_authors.iterrows():
        autor = row['Autor_norm']
        autor = str(autor).strip()
        G_sub.add_node(autor)     #Creación del nodo con el nombre
        afiliacion1 = row['Afiliacion1']
        afiliacion2 = row['Afiliacion2']
        G_sub.nodes[autor]['afiliacion1'] = str(afiliacion1).strip()    #Se agragan sus atributos
        G_sub.nodes[autor]['afiliacion2'] = str(afiliacion2).strip()

    return G_sub


def connect_Authors(G_sub, df):
    '''
    Creación y agregación de aristas que conectan coautores al grafo

    Parametros
    ---------
    G_sub : Grafo de NetworkX donde se agregarán aristas
    df: dataframe con los datos de los autores

    Returns
    -------
    G_sub: grafo modificado

    '''
    dict_coautores = defaultdict(list)

    #Diccionario donde la llave es un artículo y el valor es la lista de autores de ese artículo
    for index, row in df.iterrows():
        dict_coautores[row['Titulo']].append(row['Autor_norm'])

    #Creación de aristas con las combinaciones posibles de dos autores por cada artículo
    for titulo, list_authors in dict_coautores.items():     #Recorre cada artículo
        for i in range(0,len(list_authors)):
            for j in range(i+1,len(list_authors)):
                autor1 = str(list_authors[i]).strip()
                autor2 = str(list_authors[j]).strip()
                if autor1 in list(G_sub[autor2]):         #Si ya existe la arista continúa
                    continue
                else:
                    G_sub.add_edge(autor1,autor2)         #Creación de la arista

    return G_sub


def createSubGraph(dataframe):
    '''
    Creación y agregación de aristas que conectan coautores al grafo

    Parametros
    ---------
    dataframe: dataframe de la base de datos

    Returns
    -------
    G_sub: grafo modificado

    '''
    G_sub = nx.Graph()        #Creación de una instancia de Graph

    df = dataframe
    df_authors = df[['Autor_norm','Afiliacion1','Afiliacion2']]
    df_authors = df_authors.fillna(0)               #Llena los espacios en blanco con 0´s
    df_authors = df_authors.drop_duplicates()

    # --- Agregar nodos de autores ---
    G_sub = addAuthor(G_sub, df_authors)

    # --- Conectar autores ---
    G_sub = connect_Authors(G_sub, df)

    return G_sub