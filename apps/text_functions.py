import contextlib
import networkx as nx
import pandas as pd
import numpy as np
import math as mt
from nltk.tag import pos_tag
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.corpus import stopwords         # Librería para ayudar al filtrado de datos, excluyendo palabras comunes
import re

from nltk.stem import SnowballStemmer
sb_stemmer = SnowballStemmer("english",)  # Reducción de palabras con una misma raíz

from sumy.summarizers.text_rank import TextRankSummarizer
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer

summarizer = TextRankSummarizer()

from nltk.collocations import BigramCollocationFinder
from nltk.metrics import BigramAssocMeasures

def filtrarTexto(texto):
    '''Obtención de palabras significativas de un texto.

    Parametros
    ---------
    texto: cadena a filtrar

    Returns
    -------
    words: lista de palabras significativas
    '''
    words = []
    list_texto = pos_tag(word_tokenize(texto.lower()),tagset='universal')
    for palabra in list_texto:
        if (palabra[1] in ['NOUN', 'ADJ', 'X', 'NUM'] and palabra[0] not in stopwords.words("english")
            and re.search('[a-zA-Z]', palabra[0]) and len(palabra[0]) > 1
            and not re.search('[a-zA-Z0-9]{1}[+-][a-zA-Z0-9]{1}|[\/.]|[0-9]{3,}', palabra[0])):
            if any(map(str.isdigit, palabra[0])) and re.search('^[a-zA-Z][0-9]|[0-9][a-zA-Z]$', palabra[0]):
                words.append(palabra[0])
            elif not any(map(str.isdigit, palabra[0])):
                if not re.search('^[a-zA-Z][^0-9a-zA-Z]+$', palabra[0]):
                    if not str(palabra[0]).startswith('\\') and not re.search('^[+-][0-9a-zA-Z]+$', palabra[0]):
                        words.append(sb_stemmer.stem(palabra[0]))
    return words

def getKeywords(G: nx.Graph, articulo: str):
    """Función que obtiene las keywords conectadas directamente a un artículo dado

    Parametros
    ----------
        G: Grafo completo
        articulo: Artículo dentro del grafo G cuyas keywords se desean conocer

    Returns
    -------
        list_keywords: Lista de las keywords obtenidas
    """
    list_keywords = []
    try:
        list_keywords.extend(
            keyword
            for keyword in G.neighbors(articulo)
            if G.nodes[keyword]['tipo'] == 'keyword'
        )
    except Exception as e:
        print(e)
    return list_keywords

# ------------------------------ Similitud de artículos ---------------------------------------
def similitudArticulosByKeywords(G: nx.Graph, articulo_x: str, articulo_y: str):
    """Obtiene la similitud entre dos artículos contenidos en el grafo G, en base a sus keywords

    Parametros
    ----------
        G: Grafo completo
        articulo_x: Primer artículo
        articulo_y: Segundo artículo

    Returns
    -------
        Simulitud: Similitud por coseno de los artículos dados en base a las keywords
    """
    keywords_x = getKeywords(G, articulo_x)
    keywords_y = getKeywords(G, articulo_y)
    vector_keywords = getKeywords(G, articulo_x)
    Xi = 0
    Yi = 0
    XY = 0

    if len(keywords_x) != 0 or len(keywords_y) != 0:    #si hay keywords
        for keyword in keywords_y:
            if keyword not in vector_keywords:     #se hace un vector de la unión de las keywords de ambos artículos
                vector_keywords.append(keyword)

        matriz = pd.DataFrame(columns = vector_keywords, index = ['x','y'])       #matriz con las keywords como columnas y los artículos como filas
        for keyword in vector_keywords:         #se coloca un 1 en la matriz si la keyword se encuentra en algún artículo
            if keyword in keywords_x:
                matriz.loc['x',keyword] = 1
            if keyword in keywords_y:
                matriz.loc['y',keyword] = 1
        matriz = matriz.fillna(0)

        for keyword,articulo in matriz.items():
            XY += articulo[0]*articulo[1]           #producto escalar de los vectores de los artículos
            Xi += pow(articulo[0],2)                #sumatoria de los cuadrados del vector del artículo X
            Yi += pow(articulo[1],2)                #sumatoria de los cuadrados del vector del artículo Y

        return XY/mt.sqrt(Xi*Yi)                     #función coseno
    return 0        #si no hay keywords la similitud es cero

def similitudArticulosByAbstract(G: nx.Graph, articulo_x: str, articulo_y: str):
    """Obtiene la similitud entre dos artículos contenidos en el grafo G, en base a los abstract

    Parametros
    ----------
        G: Grafo completo
        articulo_x: Primer artículo
        articulo_y: Segundo artículo

    Returns
    -------
        Simulitud: Similitud por coseno de los artículos dados en base a los abstract
    """
    words_x = []
    words_y = []
    try:
        words_x = filtrarTexto(G.nodes[articulo_x]['Abstract'])
        words_y = filtrarTexto(G.nodes[articulo_y]['Abstract'])
    except Exception as e:
        return -1
    vector_words = filtrarTexto(G.nodes[articulo_x]['Abstract'])
    Xi = 0
    Yi = 0
    XY = 0

    if len(words_x) != 0 or len(words_y) != 0:    #si después del filtrado quedaron palabras
        for Word in words_y:
            if Word not in vector_words:     #se hace un vector de la unión de las palabras de ambos artículos
                vector_words.append(Word)

        matriz = pd.DataFrame(columns = vector_words, index = ['x','y'])       #matriz con las palabras como columnas y los artículos como filas
        for Word in vector_words:           #se coloca un 1 en la matriz si la palabra se encuentra en algún artículo
            if Word in words_x:
                matriz.loc['x',Word] = 1
            if Word in words_y:
                matriz.loc['y',Word] = 1
        matriz = matriz.fillna(0)

        for Word, articulo in matriz.items():
            XY += articulo[0]*articulo[1]           #producto escalar de los vectores de los artículos
            Xi += pow(articulo[0],2)                #sumatoria de los cuadrados del vector del artículo X
            Yi += pow(articulo[1],2)                #sumatoria de los cuadrados del vector del artículo Y

        return XY/mt.sqrt(Xi*Yi)                     #función coseno
    return 0        #si no hay palabras después del filtrado la similitud es cero

# ------------------------------ Text summarization ---------------------------------------
def textSummarization(Abstract):
    """Obtención del resumen del Abstract de un artículo"""
    parser = PlaintextParser.from_string(Abstract,Tokenizer("english"))
    summary = summarizer(parser.document,2)
    return "".join(str(sentence) for sentence in summary)

# ------------------------------ Pregunta técnica ----------------------------------------

# ------------------------- corpus y lista de BiGrams ------------------------------------

def createCorpus(df):
    """Genera un corpus con todas las palabras relevantes dentro de los artículos
    Parametros
    ----------
    df: DataFrame cargado originalmente

    Returns
    -------
    texto_filtrado: cadena de todas las palabras relevantes, separadas por espacio
    """
    texto_filtrado = ''
    df = df[['Titulo','Keywords','Abstract']].drop_duplicates()
    df = df.fillna(0)
    for index, row in df.iterrows():
        texto = str(row['Titulo'])
        if row['Keywords'] != 0:
            keywords = str(row['Keywords']).replace(';', '')
            texto += keywords
        if row['Abstract'] != 0:
            texto += str(row['Abstract'])
        list_words = filtrarTexto(texto)
        for word in list_words:
            texto_filtrado += f'{word} '
    return texto_filtrado

def foundBiGrams(texto):
    finder = BigramCollocationFinder.from_words(filtrarTexto(texto))
    finder.apply_freq_filter(4)
    finder.score_ngrams(BigramAssocMeasures.raw_freq)

    top_collocations = finder.nbest(BigramAssocMeasures.raw_freq,2000)

    return [
        collocation[0] + ' ' + collocation[1]
        for collocation in top_collocations
        if collocation[0] != collocation[1]
    ]

# ------------------------------- Funciones para la pregunta técnica ------------------------------    

def termFrecuency(texto, palabra):
    '''
    Contador de frencuencia de una palabra en un texto.

    Parametros
    ---------
    texto: lista de palabras donde se buscará
    palabra: palabra a buscar

    Returns
    -------
    count: número de veces que aparece la palabra

    '''
    count = 0
    for word in texto:
        if word == palabra:
            count +=1
    return count

def multiwordTokenization(texto, list_collocations):
    '''
    Tokenización de las palabras significativas en un texto incluyendo tokens de una y dos palabras.

    Parametros
    ---------
    texto: cadena a tokenizar

    Returns
    -------
    tokens: lista de tokens significativos en el texto

    '''
    words = filtrarTexto(texto)
    tokens = []

    while len(words) > 0:
        if len(words) > 1:
            new_word = words[0] + ' ' + words[1]
            if new_word in list_collocations:
                tokens.append(new_word)
                words.remove(words[0])
                words.remove(words[0])
            else:
                tokens.append(words[0])
                words.remove(words[0])
        else:
            tokens.append(words[0])
            words.remove(words[0])
    return tokens

def getWords(articulo, G, list_collocations):
    '''
    Obtención de las palabras significativas del titulo, keywords y abstract de un articulo.

    Parametros
    ---------
    articulo: nombre de articulo
    G: Grafo completo
    list_collocations: Lista de posibles BiGrams dentro de los artículos

    Returns
    -------
    list_words: lista de palabras significativas

    '''
    list_words = multiwordTokenization(articulo, list_collocations)     # Filtra el nombre del artículo
    list_abstract = []
    list_keywords = []
    try:
        abstract = G.nodes[articulo]['Abstract']
        list_abstract = multiwordTokenization(abstract)    # Filtrar el abstract
        list_words.extend(iter(list_abstract))    # Agregar las palabras del abstract a la lista de palabras
    except Exception as e:
        list_abstract = []
    with contextlib.suppress(Exception):
        keywords = getKeywords(G, articulo)          # Obtener keywords
        if len(keywords) > 1:
            for keyword in keywords:
                list_key = keyword.split(' ')
                keyword_lematized = ''.join(
                    f'{sb_stemmer.stem(partKey)} '
                    for partKey in list_key
                    if partKey not in stopwords.words()
                )
                list_keywords.append(keyword_lematized.strip())  # Agregar una keyword lematizada a la lista de keywords
        list_words.extend(iter(list_keywords))    # Agregar las keywords a la lista de palabras
    return list_words

def tokenizaArticulos(G, list_collocations):
    '''
    Obtención de las palabras significativas de todos los articulos del grafo.

    Parametros
    ---------
    G: Grafo completo
    list_collocations: Lista de posibles BiGrams dentro de los artículos

    Returns
    -------
    dict_articulos: diccionario con los titulos de los articulos como clave y una lista
                    de sus palabras significativas como valor.
    list_palabras: Una lista de todas las palabras usadas en los artículos
    '''
    dict_articulos = {}
    list_palabras = []

    for articulo in list(G.nodes()):
        if G.nodes[articulo]['tipo'] == 'articulo':
            list_palabras_nodo = getWords(articulo, G, list_collocations)
            dict_articulos[articulo] = list_palabras_nodo       # Agregar palabras como valor del artículo

            list_palabras.extend(list_palabras_nodo)

    list_palabras = list(np.unique(list_palabras))

    return dict_articulos, list_palabras

def createGlobalMatriz(G, list_collocations):
    """Función que obtiene una matriz TF/IDF general de todos los artículos disponibles
    
    Parametros
    ----------
    G: Grafo Completo
    list_collocations: Lista de posibles BiGrams dentro de los artículos

    Returns
    -------
    df: DataFrame de la matriz TF/IDF obtenida
    """
    list_articulos, list_palabras = tokenizaArticulos(G, list_collocations)
    IDF = {}
    len_articulos = len(list_articulos)

    #Se forma la matriz TF de cada término en su artículo
    df = pd.DataFrame(index = list_articulos.keys(), columns = list_palabras)
    for titulo, row in df.iterrows():
        for palabra in list_articulos[titulo]:
            #row[palabra] = termFrecuency(titulo,palabra)
            row[palabra] = termFrecuency(list_articulos[titulo], palabra)
    df = df.fillna(0)

    #Se calcula el IDF de los términos
    for palabra, column in df.items():
        IDF[palabra] = 0
        for i in range(len_articulos):
            if column[i] != 0:
                IDF[palabra] += 1
        if IDF[palabra] != 0:
            IDF[palabra] = mt.log(len_articulos/IDF[palabra])

    #Se obtiene la matriz TF*IDF
    for palabra, column in df.items():
        df[palabra] *= IDF[palabra]
    
    return df

def answerQuestion(df, pregunta, list_collocations):
    '''
    Obtención de articulos que responden una pregunta de acuerdo a su similitud por
    producto escalar utilizando su matriz TF*IDF.

    Parametros
    ---------
    df: DataFrame de la matriz TF/IDF completa
    pregunta: cadena a responder
    list_collocations: Lista de posibles BiGrams dentro de los artículos

    Returns
    -------
    df: DataFrame con los 5 mejores artículos que pueden responder la pregunta
    '''

    #se obtienen los terminos de la pregunta
    list_pregunta = multiwordTokenization(pregunta, list_collocations)

    #si hay un termino de la pregunta que no esta en la matriz se agrega
    #por ende su term frecuency en los articulos sería 0
    for palabra in list_pregunta:
        if palabra not in df.columns:
            df[palabra] = 0

    #se forma el vector de terminos de la pregunta con los terminos de la matriz
    df_q = pd.DataFrame(index = [pregunta], columns = df.columns)

    #se obtiene el valor TF*IDF de los terminos en el vector pregunta
    for palabra, column in df_q.items():
        frecuencia = termFrecuency(list_pregunta,palabra)
        df_q.loc[pregunta, palabra] = frecuencia     #valor TF

        if frecuencia != 0:        #Si TF es diferente de 0 se obtiene su IDF
            IDF_count = 0
            for i in df[palabra]:               #se busca en cuantos articulos aparece esa palabra
                if i != 0:
                    IDF_count += 1
            if IDF_count != 0:                  #si aparece en algun articulo se calcula su IDF y se multiplica por TF
                df_q.loc[pregunta,palabra] *= mt.log(len(df)/IDF_count)
            else:                               #si no aparece en algun articulo, su TF*IDF es 0
                df_q.loc[pregunta,palabra] = 0

    #Se calcula la matriz TF*IDF considerando Q
    #Y se calcula similitud sumando los valores de cada vector en la matriz
    df['similitud'] = 0
    for titulo,row in df.iterrows():
        res = list(map(lambda x, y: x*y,list(row.values),list(df_q.iloc[0].values)))
        #df.loc[titulo][0:-1] = res
        df.loc[titulo,'similitud'] = sum(res)

    #Se ordenan de mayor a menor similitud y se muestran
    df = df.sort_values(by=['similitud'],ascending=False)
    df = df.drop(df[df['similitud']==0].index)
    return df.head()
