import pandas as pd
import networkx as nx
import numpy as np

from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report
from sklearn.metrics import confusion_matrix
from sklearn.neighbors import KNeighborsClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.tree import DecisionTreeClassifier
from sklearn.svm import SVC
from sklearn.svm import LinearSVC
from sklearn.model_selection import train_test_split
from keras.layers import Layer, Dense, Softmax
from keras import backend as K
from keras import Sequential
from sklearn.model_selection import RandomizedSearchCV
from sklearn.metrics import accuracy_score, mean_squared_error, precision_recall_fscore_support

scaler = StandardScaler()

from apps import features as ft

#----- Modelos -----
class RBFLayer(Layer):
    '''
    Una clase de capa para utilizar RBF(Radial Basis Function) en un modelo de Keras.

    Parameters
    ----------

    :units int:
        Cantidad de unidades de la capa.

    :gamma float:
        Parametro de influencia en la Función de base radial.

    '''

    def __init__(self, units, gamma, **kwargs):
        super(RBFLayer, self).__init__(**kwargs)
        self.units = units
        self.gamma = K.cast_to_floatx(gamma)

    def build(self, input_shape):
        self.mu = self.add_weight(name='mu',
                                  shape=(int(input_shape[1]), self.units),
                                  initializer='uniform',
                                  trainable=True)
        super(RBFLayer, self).build(input_shape)

    def call(self, inputs):
        diff = K.expand_dims(inputs) - self.mu
        l2 = K.sum(K.pow(diff,2), axis=1)
        res = K.exp(-1 * self.gamma * l2)
        return res

    def compute_output_shape(self, input_shape):
        return (input_shape[0], self.units)

# Definición de la red RBF
model = Sequential()
model.add(Dense(20, input_shape=(7,),activation = 'relu'))
model.add(RBFLayer(20, 0.5, input_shape=(20,)))
model.add(Dense(1, input_shape=(20,), activation = 'sigmoid'))
model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])

def transformVariables(data, data_test):
    '''Función que normaliza los valores de los dataFrame de test y train para usarlos en los modelos de Machine Learning'''
    #data = pd.read_csv('sample_features_train.csv', index_col = 0)
    #data_test = pd.read_csv('sample_features_test.csv', index_col = 0)

    # Variables a considerar, ignoramos el shortest_path_length
    variables = data[['sum_of_neighbors', 'log_secundary_neighbors', 'sum_of_keywords',
        'keywords_match', 'clustering_index_sum', 'jaccard_coefficient',
        'community_ra', 'connected']]
    scaler = StandardScaler()

    X_train = scaler.fit_transform(data[['sum_of_neighbors', 'log_secundary_neighbors', 'sum_of_keywords',
        'keywords_match', 'clustering_index_sum', 'jaccard_coefficient',
        'community_ra']].values)
    y_train = data['connected'].values

    X_test = scaler.fit_transform(data_test[['sum_of_neighbors', 'log_secundary_neighbors', 'sum_of_keywords',
        'keywords_match', 'clustering_index_sum', 'jaccard_coefficient',
        'community_ra']].values)
    y_test = data_test['connected'].values

    X_train_nb = data[['sum_of_neighbors', 'log_secundary_neighbors', 'sum_of_keywords',
        'keywords_match', 'clustering_index_sum', 'jaccard_coefficient',
        'community_ra']].values
    
    return runModels(X_train, y_train, X_test, y_test)

# Definición de modelos
modelos_nombres = ["Decision Tree",
                   "SVM - Linear Kernel",
                   "SVM - RBF Kernel",
                   "K-Neighbors",
                   "Naive Bayes",
                   "Multi-Layer Perceptron"
                  ]

modelos = [RandomizedSearchCV(#Decision Tree
                estimator = DecisionTreeClassifier(),
                param_distributions =
                {
                   "criterion": ["entropy","gini"],               #gini, entropy, log_loss - default:gini - La funcion para medir la calidad de una division
                   "max_depth":[2,4,6, None],                     #Maxima profundidad del arbol
                   "min_samples_leaf":[60,70,80,90,100,110,120],  #El numero minimo de nodos muestra para estar en un nodo hoja
                   "max_features":["sqrt"]                 #auto, sqrt, log2 - default:Nose - El numero de funciones a considerar cuando se busca la mejor division
                },
                n_iter=60,
                cv=10,
                verbose=0,
                random_state=42,
                n_jobs=-1),
           RandomizedSearchCV(#SVM - Linear
                estimator = LinearSVC(),
                param_distributions =
                {
                   "C" : [0.0001, 0.0005, 0.001, 0.005, 0.01, 0.05, 0.1, 1.0],   #parametro de regularizacion
                   "dual": [False]                                               #Seleccionar el algoritmo para resolver el problea de optimizacion dual o primario. dual = False cuando n_samples > n_features
                },
                n_iter=30,
                cv=10,
                verbose=0,
                random_state=42,
                n_jobs=-1),
            RandomizedSearchCV(#SVM - RBF  - Es el optimo anterior, toma mucho tiempo ejecutarlo.
                estimator = SVC(),
                param_distributions =
                {
                   "kernel": ["rbf"],        #Tipo de kernel utilizado - linear, poly, rbf, sigmoid, precomputed - default = rbf
                   "C" : [5.3],              #parametro de regularizacion
                   "gamma" : ['auto'],       #Coeficiente de kernel para rbf, poly y sigmoid. Auto = 1/n_features
                   "class_weight" : [None]   #
                },
                n_iter=30,
                cv=10,
                verbose=0,
                random_state=42,
                n_jobs=-1),
            RandomizedSearchCV(#K-Neighbors
                estimator = KNeighborsClassifier(),
                param_distributions =
                {
                   "n_neighbors": list(range(28,50)),    #Numero de vecinos a usar para las busquedas
                   "weights" : ['uniform', 'distance'],  #uniform, distance, callable, None - default = uniform
                                                         #uniform: Pesos uniformes, todos los puntos en cada vecindario tienen el mismo peso
                                                         #distance: el peso de los puntos por la inversa de la distancia
                   "metric" : ['minkowski'],             #str, callable - default: minkowski (p=2)
                   "p" : [1,2,3,4,5]                     #Parametro para la metrica de Minkowski
                },
                n_iter=100,
                cv=10,
                verbose=0,
                random_state=42,
                n_jobs=-1),
           GaussianNB(),
           MLPClassifier()
          ]

def runModels(X_train, y_train, X_test, y_test):
    '''Función que corre los modelos.
    Los modelos son entrenados con los datos normalizados de train, y posteriormente son evaluados usando los datos normalizados de test'''
    resultados = []
    resultados_pos = []
    bagging = np.zeros_like(y_test)
    bp = {}

    bandera_cv = False
    modelos_finales = []

    for i, modelo in enumerate(modelos):
        #print(modelos_nombres[i])
        #print(str(modelo))
        modelo.fit(X_train, y_train)
        y_pred = modelo.predict(X_test)
        bagging += y_pred.reshape(len(y_pred))
        try:
            bp[modelos_nombres[i]] = modelo.best_params_
            #print("Mejores parámetros en CV Randomized Search:")
            #print(modelo.best_params_)
            modelos_finales.append(modelo.best_estimator_)
            bandera_cv = True
        except:
            pass #Cuando no es CV
        if not bandera_cv:
            modelos_finales.append(modelo)
        bandera_cv = False

        #print(classification_report(y_test, y_pred, target_names=['Colaboro', 'No colaboro']))
        p, r, f, _ = precision_recall_fscore_support(y_test, y_pred, average = 'weighted')
        p_pos, r_pos, f_pos, _ = precision_recall_fscore_support(y_test, y_pred, pos_label=None)
        resultados.append([modelos_nombres[i],
                        accuracy_score(y_test, y_pred),
                        p,
                        r,
                        f,
                        mean_squared_error(y_test, y_pred)])
        resultados_pos.append([modelos_nombres[i],
                        accuracy_score(y_test, y_pred),
                        p_pos[0],
                        r_pos[0],
                        f_pos[0],
                        mean_squared_error(y_test, y_pred)])


    model.fit(X_train, y_train, epochs=100, verbose=False)
    modelos_finales.append(model)

    y_pred = np.round(model.predict(X_test))
    np.add(bagging, y_pred.reshape(len(y_pred)), casting='unsafe')
    #bagging += y_pred.reshape(len(y_pred))
    loss,accuracy = model.evaluate(X_test, y_test,)
    #print(f"RBF Network Accuracy: {accuracy}")
    p, r, f, _ = precision_recall_fscore_support(y_test, y_pred, average = 'weighted')
    resultados.append(["RBF Network",
                        accuracy_score(y_test, y_pred),
                        p,
                        r,
                        f,
                        mean_squared_error(y_test, y_pred)])
    p_pos, r_pos, f_pos, _ = precision_recall_fscore_support(y_test, y_pred, pos_label=None)
    resultados_pos.append(["RBF Network",
                        accuracy_score(y_test, y_pred),
                        p_pos[0],
                        r_pos[0],
                        f_pos[0],
                        mean_squared_error(y_test, y_pred)])

    y_pred = bagging > 3.0
    p, r, f, _ = precision_recall_fscore_support(y_test, y_pred, average = 'weighted')
    p_pos, r_pos, f_pos, _ = precision_recall_fscore_support(y_test, y_pred, pos_label=None)
    resultados.append(["Bagging",
                        accuracy_score(y_test, y_pred),
                        p,
                        r,
                        f,
                        mean_squared_error(y_test, y_pred)])
    resultados_pos.append(["Bagging",
                        accuracy_score(y_test, y_pred),
                        p_pos[0],
                        r_pos[0],
                        f_pos[0],
                        mean_squared_error(y_test, y_pred)])

    res_bal = pd.DataFrame(resultados, columns=['Clasificador', 'Accuracy', 'Precision', 'Recall', 'F1 Score', 'Squared Error'])
    res_pos = pd.DataFrame(resultados_pos, columns=['Clasificador', 'Accuracy', 'Precision', 'Recall', 'F1 Score', 'Squared Error'])

    #res_bal.to_csv('resultados_balanceados.csv')
    #res_pos.to_csv('resultados_positivos.csv')

    return modelos_finales, res_bal, res_pos

#data = pd.read_csv('sample_features_train.csv', index_col = 0)
#data_test = pd.read_csv('sample_features_test.csv', index_col = 0)

#transformVariables(data, data_test)

def predecir(autor1,autor2, G, G_sub, data_test, modelos):
    if autor1 not in G_sub.neighbors(autor2):
        # 1. Obtención de parámetros
        sum_neighbors = len(ft.neighbors(G,autor1)) + len(ft.neighbors(G,autor2))
        sec_neighbors = ft.sum_sec_neig(G,autor1,autor2)
        sum_kw = len(ft.sum_keywords(G,autor1,autor2))
        kw_match = len(ft.keyword_match(G,autor1,autor2))
        clus_index = ft.clustering_index(G_sub,autor1,autor2)
        jacc_coeff = ft.jaccard_coefficient(G_sub,autor1,autor2)
        comm_ra = ft.community_ra(G_sub,autor1,autor2)
        registro = np.array([[sum_neighbors, sec_neighbors, sum_kw, kw_match, clus_index, jacc_coeff, comm_ra]])

        # 2. Creación de DataFrame
        registro = pd.DataFrame(registro, columns = ['sum_of_neighbors',
                  'log_secundary_neighbors',
                  'sum_of_keywords',
                  'keywords_match',
                  'clustering_index_sum',
                  'jaccard_coefficient',
                  'community_ra'])

        X_test = data_test[['sum_of_neighbors',
                  'log_secundary_neighbors',
                  'sum_of_keywords',
                  'keywords_match',
                  'clustering_index_sum',
                  'jaccard_coefficient',
                  'community_ra']]

        # 3. Concatenación de DataFrames
        df = pd.concat([X_test, registro]).reset_index(drop=True)
       
        # 4. Normalización de valores
        prueba = scaler.fit_transform(df.values)
        prueba = pd.DataFrame(prueba)
        
        # 5. Separación de la última fila
        prueba = prueba.tail(n=1).values
        
        resultadosList = []
        for modelo in modelos:
            # 6. Predicción
            res = modelo.predict(prueba)
            resultadosList.append(res[0])

        res = model.predict(prueba)
        resultadosList.append(res[0][0])
        resultadosLinkPrediction = {
            'Clasificador': [
                'Decision Tree',
                'SVM - Linear Kernel',
                'SVM - RBF Kernel',
                'K-Neighbors',
                'Naive Bayes',
                'Multi-Layer Perceptron',
                'RBF - Network',
            ],
            'Respuesta': resultadosList,
        }
        return resultadosLinkPrediction
    else:
        {}