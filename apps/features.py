import networkx as nx
from math import log
import numpy as np

# Libreria creada para optimizar el codigo al momento de obtener los parametros para los modelos, y para consultas predictivas

def neighbors(G,node):
    """
    Obtiene los vecinos del autor dado, usando una estructura de Grafo
    
    Parametros
    ----------
    G : Grafo de NetworkX
    node : Autor como nodo del grafo G

    Returns
    -------
    list_neighbors : Una lista de los vecinos del autor dentro del grafo G

    """
    list_neighbors = []         # Lista de vecinos a través de los artículos
    list_neighbors_unique = []  # Lista de vecinos sin repeticiones
    for articulo in G.neighbors(node):
        try:
            if G.nodes[articulo]['tipo'] == 'articulo':             # Ir primero hacia los artículos que conectan al autor
                for autor_vecino in G.neighbors(articulo):
                    try:
                        if G.nodes[autor_vecino]['tipo'] == 'autor':    # Partir de los artículos hacia los otros autores
                            if autor_vecino != node:
                                list_neighbors.append(autor_vecino)
                    except Exception as e:
                        print(autor_vecino, e)
        except Exception as e:
            print(node, e)
    # Eliminar repeticiones
    for vecino in list_neighbors:
        if vecino not in list_neighbors_unique:
            list_neighbors_unique.append(vecino)
    return list_neighbors_unique

def extract_sec_neig(G,node):
    """
    Devuelve el conteo del número total de los vecinos secundarios de un autor en un Grafo G

    Parametros
    ----------
    G : Grafo de NetworkX
    node : Autor como nodo del grafo G

    Returns
    -------
    count : Total de vecinos secundarios de un nodo

    """
    list_neighbors = neighbors(G,node)
    count = 0
    # Obtener los vecinos secundarios
    for neighbor_prin in list_neighbors:
        count = count + len(neighbors(G,neighbor_prin))
    if count == 0:
        return 1
    return count

def sum_sec_neig(G,node_a,node_b):
    """
    Devuelve la suma de los logaritmos en base e de los vecinos secundarios de un par de nodos (autores)

    Parametros
    ----------
    G : Grafo de NetworkX
    node_a : Autor 1 en forma de nodo del grafo G
    node_b : Autor 2 en forma de nodo del grafo G

    Returns
    -------
    Suma de los logaritmos en base e de los vecinos secundarios de un par de nodos

    """
    try:
        return log(extract_sec_neig(G,node_a))+log(extract_sec_neig(G,node_b))
    except Exception as e:
        print(e)
        print(node_a,'_',node_b)

def keywords(G,node):
    """
    Obtiene las keywords de los artículos, partiendo de un nodo autor

    Parametros
    ----------
    G : Grafo de NetworkX
    node : Autor como nodo del grafo G

    Returns
    -------
    list_keywords : Lista de las keywords que uso un autor a lo largo de todos sus artículos
    
    """
    list_keywords = []         
    for articulo in G.neighbors(node):
        try:
            if G.nodes[articulo]['tipo'] == 'articulo':             # Ir primero hacia los artículos que conectan al autor
                for keyword in G.neighbors(articulo):
                    try:
                        if G.nodes[keyword]['tipo'] == 'keyword':    # Partir de los artículos hacia las keywords
                            list_keywords.append(keyword)
                    except Exception as e:
                        print(keyword, e)
        except Exception as e:
            print(node, e)
    return list_keywords

def sum_keywords(G,node_a,node_b):
    """
    Devuelve las keywords que usaron un par de autores

    Parametros
    ---------
    G : Grafo de NetworkX
    node_a : Autor 1 en forma de nodo del grafo G
    node_b : Autor 2 en forma de nodo del grafo G

    Returns
    -------
    keywords_a : Lista de las keywords usadas por un par de autores en todos sus artículos

    """
    keywords_a = keywords(G,node_a)
    keywords_b = keywords(G,node_b)
    
    for keyword in keywords_b:
        keywords_a.append(keyword)
    
    keywords_a = np.unique(keywords_a)
    return keywords_a

def keyword_match(G,node_a,node_b):
    """
    Obtiene las keywords en comun que usaron un par de autores

    Parametros
    ---------
    G : Grafo de NetworkX
    node_a : Autor 1 en forma de nodo del grafo G
    node_b : Autor 2 en forma de nodo del grafo G

    Returns
    -------
    list_keywords : Lista de las keywords en común usadas por un par de autores en todos sus artículos

    """
    keywords_a = keywords(G,node_a)
    keywords_b = keywords(G,node_b)
    unique_keywords = sum_keywords(G,node_a,node_b)
    list_keywords = []
    
    for keyword in unique_keywords:
        if keyword in keywords_a and keyword in keywords_b:
            list_keywords.append(keyword)
    return list_keywords

def areas(G,node):
    """
    Obtiene las areas en las que el autor ha trabajado en sus artículos

    Parametros
    ----------
    G : Grafo de NetworkX
    node : Autor como nodo del grafo G

    Returns
    -------
    list_areas : Lista de las areas en las que el autor ha desarrollado sus articulos

    """
    list_areas = []         
    for articulo in G.neighbors(node):
        try:
            if G.nodes[articulo]['tipo'] == 'articulo':             # Ir primero hacia los artículos que conectan al autor
                list_areas.append(G.nodes[articulo]['Area'])
        except Exception as e:
            print(node, e)
    return list_areas

def sum_areas(G,node_a,node_b):
    """
    Obtiene la suma de areas en las que un par de autores ha desarrollado sus articulos

    Parametros
    ---------
    G : Grafo de NetworkX
    node_a : Autor 1 en forma de nodo del grafo G
    node_b : Autor 2 en forma de nodo del grafo G

    Returns
    -------
    list_areas : Lista de las areas en las que un par de autores han desarrollado sus articulos

    """
    areas_a = areas(G,node_a)
    areas_b = areas(G,node_b)
    
    # Eliminar repeticiones
    for area in areas_b:
        areas_a.append(area)
    
    areas_a = np.unique(areas_a)
    return areas_a

def extract_lenght_short_path(G_sub,list_nodes):
    """
    Devuelve la distancia mas corta entre un par de nodos

    Parametros
    ---------
    G_sub : Grafo de NetworkX
    list_nodes : Tupla de autores en forma de nodos del grafo G

    Returns
    -------
    length : Distancia mas corta entre un par de autores, o Nan
    
    """
    node_a,node_b = list_nodes[0],list_nodes[1]
    try:
        return nx.single_source_shortest_path_length(G_sub,node_a)[node_b]
    except Exception as e:
        print(e)
        return np.nan
    
def clustering_index(G_sub,node_a,node_b):
    """
    Obtiene el clustering index de un par de autores
    
    Parametros
    ---------
    G_sub : Grafo de NetworkX
    node_a : Autor 1 en forma de nodo del grafo G_sub
    node_b : Autor 2 en forma de nodo del grafo G_sub

    Returns
    -------
    sum clustering : La suma del valor de clustering index de un par de autores

    """
    d = nx.clustering(G_sub, nodes=[node_a,node_b])
    return sum(d.values())

def jaccard_coefficient(G_sub,node_a,node_b):
    """
    Devuelve el Jaccard coeficient de un par de autores

    Parametros
    ---------
    G_sub : Grafo de NetworkX
    node_a : Autor 1 en forma de nodo del grafo G_sub
    node_b : Autor 2 en forma de nodo del grafo G_sub

    Returns
    -------
    sum jaccard : La suma del valor de Jaccard Coefficient de un par de autores

    """
    d = list(nx.jaccard_coefficient(G_sub,[(node_a,node_b)]))
    return d[0][2]

def get_resource_allocation_index(G_sub,node_a,node_b):
    """
    Devuelve el resource allocation index de un par de autores

    Parametros
    ---------
    G_sub : Grafo de NetworkX
    node_a : Autor 1 en forma de nodo del grafo G_sub
    node_b : Autor 2 en forma de nodo del grafo G_sub

    Returns
    -------
    sum resource : La suma del valor de resource allocation index de un par de autores

    """
    d = list(nx.resource_allocation_index(G_sub,[(node_a,node_b)]))
    return d[0][2]

def get_adamic_adar_index(G_sub,node_a,node_b):
    """
    Devuelve el adamic adar index de un par de autores

    Parametros
    ---------
    G_sub : Grafo de NetworkX
    node_a : Autor 1 en forma de nodo del grafo G_sub
    node_b : Autor 2 en forma de nodo del grafo G_sub

    Returns
    -------
    sum adamix adar : La suma del valor de adamic adar index de un par de autores

    """
    d = list(nx.adamic_adar_index(G_sub,[(node_a,node_b)]))
    return d[0][2]

def get_preferential_attachment(G_sub,node_a,node_b):
    """
    Devuelve el preferential attachment index de un par de autores

    Parametros
    ---------
    G_sub : Grafo de NetworkX
    node_a : Autor 1 en forma de nodo del grafo G_sub
    node_b : Autor 2 en forma de nodo del grafo G_sub

    Returns
    -------
    sum preferential attachment : La suma del valor de preferential attachment index de un par de autores

    """
    d = list(nx.preferential_attachment(G_sub,[(node_a,node_b)]))
    return d[0][2]

def community_cn(G_sub,node_a,node_b):
    """
    Devuelve la suma de los vecinos en comun por comunidades

    Parametros
    ---------
    G_sub : Grafo de NetworkX
    node_a : Autor 1 en forma de nodo del grafo G_sub
    node_b : Autor 2 en forma de nodo del grafo G_sub
    
    Returns
    -------
    bonus + len(cn) : Indice de los vecinos en comun por comunidades
    
    """
    com_1a = G_sub.nodes[node_a]['afiliacion1']
    com_1b = G_sub.nodes[node_b]['afiliacion1']
    com_2a = G_sub.nodes[node_a]['afiliacion2']
    com_2b = G_sub.nodes[node_b]['afiliacion2']
    
    bonus = 0
    cn = list(nx.common_neighbors(G_sub, node_a, node_b))

    if com_1a == com_1b or com_1a == com_2b:
        for vecino in cn:
            if G_sub.nodes[vecino]['afiliacion1'] == com_1a or G_sub.nodes[vecino]['afiliacion2'] == com_1a:
                bonus += 1
    if com_2a != '0' and (com_2a == com_1b or com_2a == com_2b):
        for vecino in cn:
            if G_sub.nodes[vecino]['afiliacion1'] == com_2a or G_sub.nodes[vecino]['afiliacion2'] == com_2a:
                bonus += 1
    return bonus + len(cn)

def community_ra(G_sub,node_a,node_b):
    """
    Devuelve la suma de los vecinos en comun por comunidades, cuando ambos autores y sus vecinos en comun pertenecen a una misma comunidad

    Parametros
    ---------
    G_sub : Grafo de NetworkX
    node_a : Autor 1 en forma de nodo del grafo G_sub
    node_b : Autor 2 en forma de nodo del grafo G_sub
    
    Returns
    -------
    indice : Indice de los vecinos en comun por comunidades
    
    """
    com_1a = G_sub.nodes[node_a]['afiliacion1']
    com_1b = G_sub.nodes[node_b]['afiliacion1']
    com_2a = G_sub.nodes[node_a]['afiliacion2']
    com_2b = G_sub.nodes[node_b]['afiliacion2']
    
    indice = 0
    cn = list(nx.common_neighbors(G_sub, node_a, node_b))

    if com_1a == com_1b or com_1a == com_2b:
        for vecino in cn:
            if G_sub.nodes[vecino]['afiliacion1'] == com_1a or G_sub.nodes[vecino]['afiliacion2'] == com_1a:
                bors = len(list(G_sub.neighbors(vecino)))
                indice += (1/bors)
    if com_2a != '0' and (com_2a == com_1b or com_2a == com_2b):
        for vecino in cn:
            if G_sub.nodes[vecino]['afiliacion1'] == com_2a or G_sub.nodes[vecino]['afiliacion2'] == com_2a:
                bors = len(list(G_sub.neighbors(vecino)))
                indice += (1/bors)
    return indice