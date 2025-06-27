import pandas as pd
import networkx as nx
import numpy as np

from apps import graph_functions as gf
from apps import features as ft

#----- Filtrado de datos -----
#df_original = pd.read_csv('UNAM_Completo_Corregido.csv')
def filterAndSplit(df_original):
    #Se forma nodes_catalogue con autores con mas de 2 artículos
    nodes_catalogue =df_original[['Titulo','Autor_norm']].groupby('Autor_norm',as_index=False).count()
    nodes_catalogue = nodes_catalogue[nodes_catalogue['Titulo']>2]
    nodes_catalogue = nodes_catalogue.reset_index(drop=True)    

    #lista de autores filtrados
    autores = nodes_catalogue['Autor_norm'].to_list()

    #Datos para grafo completo con autores filtrados
    df_original = df_original[df_original['Autor_norm'].isin(autores)]
    df_original = df_original.reset_index(drop = True)
    return df_original, nodes_catalogue

def createGraphs(df_original):
    #Se separan los datos de entrenamiento y prueba
    count_per_year = df_original['Año'].value_counts().sort_index().to_dict()
    ratio = 3/4 * sum(count_per_year.values())
    count = 0
    df_train = pd.DataFrame()
        
    for i in count_per_year:
        year = i
        count += count_per_year[i]
        df_train = pd.concat([df_train,df_original[df_original['Año']==i]])
        if count > ratio:
            break
        
    df_test = df_original[df_original['Año'] > year]

    #numero de datos después del filtrado y la división
    #print('Datos de entrenamiento: ' + str(df_train.shape))
    #print('Datos de prueba: ' + str(df_test.shape))

    #----- Creación de grafos y subgrafos -----
    #Grafo completo
    G_completo = gf.createGraph(df_original)
    G_sub_completo = gf.createSubGraph(df_original)
    #nx.write_gml(G_completo, 'BD_UNAM_Graph.gml')
    #nx.write_gml(G_sub_completo, 'BD_UNAM_Sub_Graph.gml')

    #Datos de entrenamiento
    G_train = gf.createGraph(df_train)
    G_sub_train = gf.createSubGraph(df_train)

    #nx.write_gml(G_train, 'BD_UNAM_Graph_train.gml')
    #nx.write_gml(G_sub_train, 'BD_UNAM_Sub_Graph_train.gml')

    #Datos de prueba
    G_test = gf.createGraph(df_test)
    G_sub_test = gf.createSubGraph(df_test)

    #nx.write_gml(G_test, 'BD_UNAM_Graph_test.gml')
    #nx.write_gml(G_sub_test, 'BD_UNAM_Sub_Graph_test.gml')

    return G_completo, G_sub_completo, G_train, G_sub_train, G_test, G_sub_test
    # sample_train, sample_test = createSamples(G_train, G_test, nodes_catalogue)
    # return getParameters(sample_train, sample_test, G_train, G_test, G_sub_train, G_sub_test)

#----- Obtención de samples ------
# Función que determina si un par de autores están conectados a través de un artículo
def nodes_connected(G, u, v):
    common_neighbors = list(nx.common_neighbors(G, u, v))
    if len(common_neighbors) > 0:
         for neighbor in common_neighbors:
            if G.nodes[neighbor]['tipo'] == 'articulo':
                return True
    return False

#Obtener la lista de los nodos no conectados, siempre que sea menor a negativos (<20000)
def list_no_connected(G,negativos, nodes_catalogue):
    lista_no_conectados= []
    no_conectados = 0
    while no_conectados<negativos:
        a = b = ''
        while a == b or a not in G or b not in G:
                a = nodes_catalogue.Autor_norm.sample(1).values[0]
                b = nodes_catalogue.Autor_norm.sample(1).values[0]

        # Han escrito algún artículo juntos?
        con = nodes_connected(G, a, b)
        if con == False:
            lista_no_conectados.append([a,b])
            no_conectados+=1
    return lista_no_conectados

#Obtener la lista de los nodos conectados, siempre que sea menor a positivos (<20000)
def list_connected(G,positivos, nodes_catalogue):
    lista_conectados= []
    conectados = 0
    while conectados<positivos:
        a = b = ''
        while a == b:
            while a == b or a not in G or b not in G:
                a = nodes_catalogue.Autor_norm.sample(1).values[0]
                b = nodes_catalogue.Autor_norm.sample(1).values[0]

        # Han escrito algún artículo juntos?
        con = nodes_connected(G, a, b)
        if con == True:
            lista_conectados.append([a,b])
            conectados+=1
    return lista_conectados

def createSamples(G_train, G_test, nodes_catalogue):
    '''
    Generación de dos dataFrames que contienen pares de autores aleatorios, más una columna que indica si están o no conectados
    '''
    #sample de datos de entrenamiento
    N_train = 500
    tasa_positivos = 11/20
    positivos_train = round(N_train*(tasa_positivos))
    negativos_train = round(N_train*(1-tasa_positivos))

    lista_no_conectados_train = list_no_connected(G_train,negativos_train, nodes_catalogue)
    lista_conectados_train = list_connected(G_train,positivos_train, nodes_catalogue)

    #al objeto pd de nodos no conectados se le pone un titulo a las columnas
    no_conectados_train = pd.DataFrame(lista_no_conectados_train).rename(columns={0:'source',1:'target'})
    conectados_train = pd.DataFrame(lista_conectados_train).rename(columns={0:'source',1:'target'})
    conectados_train['connected'] = 1
    sample = pd.concat([conectados_train, no_conectados_train])
    sample = sample.fillna(0)
    sample = sample.drop_duplicates().reset_index(drop=True).copy()
    #print(sample.connected.value_counts(1), sample.connected.value_counts())

    #sample de datos de prueba
    N_test = 280
    positivos_test = round(N_test*(tasa_positivos))
    negativos_test = round(N_test*(1-tasa_positivos))

    lista_no_conectados_test = list_no_connected(G_test,negativos_test, nodes_catalogue)
    lista_conectados_test = list_connected(G_test,positivos_test, nodes_catalogue)

    #al objeto pd de nodos no conectados se le pone un titulo a las columnas
    no_conectados_test = pd.DataFrame(lista_no_conectados_test).rename(columns={0:'source',1:'target'})
    conectados_test = pd.DataFrame(lista_conectados_test).rename(columns={0:'source',1:'target'})
    conectados_test['connected'] = 1
    sample_test = pd.concat([conectados_test, no_conectados_test])
    sample_test = sample_test.fillna(0)
    sample_test = sample_test.drop_duplicates().reset_index(drop=True).copy()
    return sample, sample_test

def getParameters(sample, sample_test, G_train, G_test, G_sub_train, G_sub_test):
    '''
    Obtención de los parámetros para cada par de autores indicados en los samples de train y test
    '''
    sample['sum_of_neighbors'] = sample[['source','target']].apply(lambda x: len(ft.neighbors(G_train,x[0])) + len(ft.neighbors(G_train,x[1])), axis=1)
    sample_test['sum_of_neighbors'] = sample_test[['source','target']].apply(lambda x: len(ft.neighbors(G_test,x[0])) + len(ft.neighbors(G_test,x[1])), axis=1)

    sample['log_secundary_neighbors']= sample[['source','target']].apply(lambda x: ft.sum_sec_neig(G_train,x[0],x[1]), axis=1)
    sample_test['log_secundary_neighbors']= sample_test[['source','target']].apply(lambda x: ft.sum_sec_neig(G_test,x[0],x[1]), axis=1)

    sample['sum_of_keywords'] = sample[['source','target']].apply(lambda x: len(ft.sum_keywords(G_train,x[0],x[1])), axis=1)
    sample_test['sum_of_keywords'] = sample_test[['source','target']].apply(lambda x: len(ft.sum_keywords(G_test,x[0],x[1])), axis=1)

    sample['keywords_match'] = sample[['source','target']].apply(lambda x: len(ft.keyword_match(G_train,x[0],x[1])), axis=1)
    sample_test['keywords_match'] = sample_test[['source','target']].apply(lambda x: len(ft.keyword_match(G_test,x[0],x[1])), axis=1)

    sample['clustering_index_sum'] = sample[['source','target']].apply(lambda x: ft.clustering_index(G_sub_train,x[0],x[1]), axis=1)
    sample_test['clustering_index_sum'] = sample_test[['source','target']].apply(lambda x: ft.clustering_index(G_sub_test,x[0],x[1]), axis=1)

    sample['jaccard_coefficient'] = sample[['source','target']].apply(lambda x: ft.jaccard_coefficient(G_sub_train,x[0],x[1]), axis=1)
    sample_test['jaccard_coefficient'] = sample_test[['source','target']].apply(lambda x: ft.jaccard_coefficient(G_sub_test,x[0],x[1]), axis=1)

    sample['community_ra'] = sample[['source','target']].apply(lambda x: ft.community_ra(G_sub_train,x[0],x[1]), axis=1)
    sample_test['community_ra'] = sample_test[['source','target']].apply(lambda x: ft.community_ra(G_sub_test,x[0],x[1]), axis=1)

    #sample_test.to_csv('sample_features_test.csv')
    #sample.to_csv('sample_features_train.csv')

    return sample, sample_test

#filterAndSplit(pd.read_csv('UNAM_Completo_Corregido.csv'))
#G_completo, G_sub_completo, G_train, G_sub_train, G_test, G_sub_test, nodes_catalogue = filterAndSplit(pd.read_csv('UNAM_Completo_Corregido.csv'))
#sample_train, sample_test = createSamples(G_train, G_test, nodes_catalogue)
#getParameters(sample_train, sample_test, G_train, G_test, G_sub_train, G_sub_test)