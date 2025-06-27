import pandas as pd
import numpy as np
import networkx as nx

# Libreria creada para optimizar el codigo al momento de hacer las consultas descriptivas

def getNodesQuery(G, nodeType, nameAtribute):
    """
    Obtiene los nodos del tipo especificado vecinos del nodo pasado como atributo.
    
    Parametros
    ----------
    G : Grafo de NetworkX
    nodeType : tipo de los nodos a obtener
    nameAtribute: nombre del nodo central 

    Returns
    -------
    list_nodes : Una lista los nodos vecinos con e tipo especificado

    """
    list_nodes = []
    for element in G.neighbors(nameAtribute):
        if G.nodes[element]['tipo'] == nodeType:
            list_nodes.append(element)
    list_nodes = np.unique(list_nodes)
    return list_nodes



def getInfoArticle(G, articulo):
    """
    Obtiene la información almacenada en los atributos y vecinos de un nodo artículo.
    
    Parametros
    ----------
    G : Grafo de NetworkX
    articulo : nodo artículo

    Returns
    -------
    dict_atributos : diccionario donde la llave es la categoría y el valor es la información

    """
    dict_atributos = {}
    atributos = G.nodes[articulo]
    for clave, valor in atributos.items():
        if (clave) == 'tipo':
            continue
        else:
            dict_atributos[clave] = valor
    dict_atributos['keywords'] = getNodesQuery(G, 'keyword', articulo)
    return dict_atributos



def keywordFrecuency(G):
    """
    Obtiene el número de veces que aparece cada keyword del grafo.
    
    Parametros
    ----------
    G : Grafo de NetworkX

    Returns
    -------
    dic_keywords : diccionario con la keyword como llave y el número de apariciones como valor

    """
    dic_keywords = {}
    for nodo in list(G.nodes()):
        if G.nodes[nodo]['tipo'] == 'keyword':
            list_articles = getNodesQuery(G, 'articulo', nodo)
            dic_keywords[nodo] = len(list_articles)
    dic_keywords = dict(sorted(dic_keywords.items(), key = lambda x: x[1], reverse=True))
    return dic_keywords



def areaFrecuency(G):
    """
    Obtiene el número de artículos por cada área de conocimiento.
    
    Parametros
    ----------
    G : Grafo de NetworkX

    Returns
    -------
    dic_area : diccionario con el area como llave y el número de artículos como valor

    """
    dic_area = {}
    for nodo in list(G.nodes()):
        if G.nodes[nodo]['tipo'] == 'articulo':
            if G.nodes[nodo]['Area'] in dic_area:
                dic_area[G.nodes[nodo]['Area']] += 1
            else:
                dic_area[G.nodes[nodo]['Area']] = 1
    dic_area = dict(sorted(dic_area.items(), key = lambda x: x[1], reverse=True))
    return dic_area



def coAuthors(G_sub):
    """
    Obtiene el número de coautores de cada autor del grafo.
    
    Parametros
    ----------
    G_sub : Grafo de NetworkX

    Returns
    -------
    dic_authors : diccionario con los autores como llaves y el número de coautores como valor

    """
    dic_authors = dict(G_sub.degree())
    dic_authors = dict(sorted(dic_authors.items(), key = lambda x: x[1], reverse=True))
    return dic_authors

def dependenciaFrecuency(G):
    """
    Obtiene la productividad de cada dependencia del grafo.
    
    Parametros
    ----------
    G : Grafo de NetworkX

    Returns
    -------
    dic_productividad : diccionario con la afiliacion como llave y la productividad como valor

    """
    articulos_por_dep = {}
    list_articulos = []
    autores_por_dep = {}
    dic_productividad = {}
    for nodo in list(G.nodes()):
        if G.nodes[nodo]['tipo'] == 'afiliacion':
            autores_por_dep[nodo] = list(G.neighbors(nodo))
    for dep in autores_por_dep.items():
        for autor in dep[1]:
            list_articulos.extend(getNodesQuery(G, 'articulo', autor))
        articulos_por_dep[dep[0]] = list(np.unique(list_articulos))
        list_articulos = []

    #productividad = articulos por dependencia/total de autores en la dependencia
    for dep in articulos_por_dep.items():
        dic_productividad[dep[0]] = len(dep[1])/len(autores_por_dep[dep[0]]) 
    dic_productividad = dict(sorted(dic_productividad.items(), key = lambda x: x[1], reverse=True))
    return dic_productividad

def articuloAutorFrecuency(G):
    """
    Obtiene los articulos con más autores.
    
    Parametros
    ----------
    G : Grafo de NetworkX

    Returns
    -------
    dic_articles : diccionario con el articulo como llave y el número de autores como valor

    """
    dic_articles = {}
    for nodo in list(G.nodes()):
        if G.nodes[nodo]['tipo'] == 'articulo':
            dic_articles[nodo] = len(getNodesQuery(G, 'autor', nodo))
    dic_articles = dict(sorted(dic_articles.items(), key = lambda x: x[1], reverse=True))
    return dic_articles