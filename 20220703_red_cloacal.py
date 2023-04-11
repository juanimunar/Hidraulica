#!/usr/bin/env python
# coding: utf-8

# In[1]:


# Importar librerías.

import pandas as pd
import numpy as np
import geopandas
from shapely.geometry import Point, LineString


# In[2]:


# Ubicación de shapes

# links originales
nombre_objeto_links = r'C:\Users\Juan Igancio\Desktop\MD_SISU\El Trebol\GIS\SHP\20221214_ETR_DC_TRAMO.shp'

# Nodos con coordenada z
nombre_objeto_nodos = r'C:\Users\Juan Igancio\Desktop\MD_SISU\El Trebol\GIS\SHP\20221214_ETR_DC_BR.shp'

# links modificados
nombre_objeto_links2 = r'C:\Users\Juan Igancio\Desktop\MD_SISU\El Trebol\GIS\SHP\20221214_ETR_DC_TRAMO_A.shp'

# Nodos sin salida
nombre_objeto_nodos_sin_salida = r'C:\Users\Juan Igancio\Desktop\MD_SISU\El Trebol\GIS\SHP\20221214_ETR_DC_NSS.shp'

# Impulsiones
#nombre_objeto_impulsiones = r'C:\Users\jmunar.SERMAN\Desktop\long_acum\impulsiones.shp'

# DEM en formato raster
#nobmre_objeto_dem = r'C:\Users\Juan Igancio\Desktop\MD_SISU\Catamarca\GIS\20221206_CAT_DEM.tif'


# In[3]:


# Sistema de coordenadas de referencia a partir de su número EPSG.

epsg = 5346


# In[4]:


# Importar el shape de links.

links = geopandas.read_file(nombre_objeto_links)
links.to_crs(crs = epsg, inplace = True)
links.head()


# In[5]:


# Método para obtener longitudes.

links['longitud'] = links.length.round(1)
links.head()


# In[6]:


# DataFrames de puntos iniciales y finales.

puntos_iniciales = geopandas.GeoDataFrame(crs=links.crs, 
                                          geometry=list(Point(links.geometry.iloc[i].coords[0]) for i in range(len(links))))
puntos_finales = geopandas.GeoDataFrame(crs=links.crs, 
                                        geometry=list(Point(links.geometry.iloc[i].coords[1]) for i in range(len(links))))
puntos_iniciales.head()


# In[7]:


# Importar el shape de nodos. Evaluar la coordenada z (sistematizar). 

nodos = geopandas.read_file(nombre_objeto_nodos)
nodos.to_crs(crs = epsg, inplace = True)
nodos.head()


# In[8]:


# Creación un buffer de 1m de los nodos para identificar vértices iniciales y finales.
# Tener presente que hay un método llamado sjoin_nearest para realizar uniones espaciales al vecino más cercano.
# El método ahorraría realizar el buffer, incluso especifica la distancia, pero requiere instalar PyGEOS.
# PyGEOS me ha generado problemas de compatibilidad en el pasado.

distancia = 1
nodos_buff = nodos.copy()
nodos_buff.geometry = nodos.buffer(distancia)
nodos_buff.head()


# In[9]:


# Spatial Join entre nodos iniciales y finales y el buffer de los nodos.

nodos_iniciales = geopandas.sjoin(puntos_iniciales, nodos_buff, how='inner', predicate='intersects')
nodos_finales = geopandas.sjoin(puntos_finales, nodos_buff, how='inner', predicate='intersects')
nodos_iniciales.head()


# In[10]:


# Nodos iniciales y finales.

links['zi'] = pd.Series(max(nodos_iniciales['z'][i], nodos_finales['z'][i]) for i in range(0,len(links)))
links['zf'] = pd.Series(min(nodos_iniciales['z'][i], nodos_finales['z'][i]) for i in range(0,len(links)))
links['ni'] = pd.Series(nodos_iniciales.index_right[i] 
                             if nodos_iniciales['z'][i] >= nodos_finales['z'][i] 
                             else nodos_finales.index_right[i] for i in range(0,len(links)))
links['nf'] = pd.Series(nodos_iniciales.index_right[i] 
                             if nodos_iniciales['z'][i] < nodos_finales['z'][i] 
                             else nodos_finales.index_right[i] for i in range(0,len(links)))
links['pi'] = pd.Series(nodos_iniciales['geometry'][i] if nodos_iniciales['z'][i] >= nodos_finales['z'][i] 
                        else nodos_finales['geometry'][i] for i in range(len(links)) )
links['pf'] = pd.Series(nodos_iniciales['geometry'][i] if nodos_iniciales['z'][i] < nodos_finales['z'][i] 
                        else nodos_finales['geometry'][i] for i in range(len(links)) )
links.head()


# In[11]:


# Pendiente del terreno de cada tramo.

links['pend_tn'] = (links.zi-links.zf)/links.longitud
links.head()


# In[12]:


# Ventilación de cada tramo.

links['ventila'] = pd.Series(1 if ((links['pend_tn'][i] != max(links.loc[links['ni'] == links['ni'][i]]['pend_tn']))
                                   or len(links.loc[links['nf'] == links['ni'][i]]) == 0)
                            else 0 for i in range(0, len(links)))

# Corrección por tramos de salida con igual pendiente

aux = []
for i in range(len(links)):
    if (len(links.loc[links['ni'] == links['ni'][i]].loc[links['ventila'] == 1]) == 
        len(links.loc[links['ni'] == links['ni'][i]]) and 
        len(links.loc[links['nf'] == links['ni'][i]]) > 0): # Si no hay ningún ventila se asigna arbitrariamente al mayor índice
        if i == max(links.loc[links['ni'] == links['ni'][i]].index):
            aux.append(0)
        else:
            aux.append(1)
    else:
        aux.append(links['ventila'][i])     
links['ventila'] = aux
links.head()


# In[13]:


# Puntos sin salida.

puntos_sin_salida = []
for i in range(len(nodos)):
    if i not in pd.unique(links['ni']):
        puntos_sin_salida.append(i)
nodos_sin_salida = nodos.iloc[puntos_sin_salida]
nodos_sin_salida['nodo'] = [nodos_sin_salida.index[i] for i in range(len(nodos_sin_salida))]    
nodos_sin_salida


# In[14]:


# Matriz de aporte inmediata

mat_apo = pd.DataFrame(index = [i for i in range(len(links))], columns = [i for i in range(len(links))], data = 0)
for i in range(len(links)):
    if links['ventila'][i] == 0:
        mat_apo[i] = links.index.isin(pd.Series(links.index).loc[links['nf'] == links['ni'][i]])*1
    else:
        pd.Series([0]*len(links))
mat_apo.iloc[:7,:7]


# In[15]:


# Se busca incorporar el resto de los aportes iterando hasta asegurar la "propagacion" vectorial. 
# El método: while sum(sum(mat_apo[i]) + 1 if links['nf'].isin(puntos_sin_salida)[i] == True 
# else 0 for i in range(len(links))) < len(links):
# Entrega valores completos a la salida pero puede entregar valores incompletos intermedios si los tramos no están ordenados.
# Para asegurar la propagación se debería contar el número de iteraciones hasta la salida, determinar el camino más largo y
# continuar iterando los valores restantes (camimno más largo - numero de iteraciones realizadas).
# Es discutible si la validación intermedia no implica mayor esfuerzo de cómputo aunque la cantidad de iteraciones sea menor.
# Por simplicidad se itera una cantidad de veces igual a la cantidad de tramos existentes.

k = 0
for k in range(len(links)):
    for i in range(len(links)):
        for j in range(len(links)):
            if mat_apo[i][j] == 1:
                mat_apo[i] = mat_apo[i] + mat_apo[j]
                mat_apo = (mat_apo/mat_apo).fillna(0)
mat_apo.iloc[:7,:7]                


# In[16]:


# Se completa la matriz de aporte con el aporte propio de cada tramo

for i in range(len(links)):
    mat_apo[i][i] = 1
mat_apo.iloc[:7,:7]


# In[17]:


# Cálculo de longitudes acumuladas mediante matriz de aporte

long_acum_mat_apo = []
for i in range(len(links)):
    long_acum_mat_apo.append(round(sum(links['longitud']*mat_apo[i]),1))
links['long_acum'] = long_acum_mat_apo    


# In[18]:


# Cálculo de la longitud acumulada. Corta cuando la longitud acumulada en los puntos sin salida es igual a la longitud total.
# Método superado por la matriz de aporte

# long_acum = [links['longitud'][i] for i in range(len(links))]

# while sum(long_acum[i] if links['nf'][i] in puntos_sin_salida 
#          else 0 for i in range(len(links))) < sum(links['longitud']):
#    for i in range(len(links)):
#        if links['ventila'][i] == 0:
#            aux = []
#            for j in range(len(links)):
#                if links['nf'][j] == links['ni'][i]:
#                    aux.append(long_acum[j])
#                else:
#                    0
#            long_acum[i] = links['longitud'][i] + sum(aux)
#        else:
#            continue
#
#links['long_acum'] = long_acum
#links.head()


# In[19]:


# Verificación de longitudes acumuladas paso 1

aux = []
for i in range(len(links)):
    if links['nf'][i] in puntos_sin_salida:
        aux.append(long_acum_mat_apo[i])
round(sum(aux),2)


# In[20]:


# Verificación de longitudes acumuladas paso 2

round(sum(links['longitud']),2)


# In[21]:


# Drop de columnas

links.drop(['id'], axis=1, inplace=True)
links.head()


# In[22]:


# Modificación del sentido de los links para que coincidan ni y nf.

links.set_geometry([LineString([links['pi'][i], links['pf'][i]],) for i in range(len(links))], inplace=True)
links.head()


# In[23]:


# Se añade una columna "invierte" para modificación manual posterior de zonas sin salida.

links['invierte'] = pd.Series(False for i in range(len(links)))
links.head()


# In[24]:


# Se crea un segundo dataframe links2, esto tiene dos objetivos.
# 1. Se pretende exportar el dataframe pero las múltiples columnas de geometría generan conflictos en la exportación.
# 2. Se desea mantener la mayor cantidad de datos posibles del dataframe links a la vez que utilizarlo como auxiliar de cálculo.

links2 = links.copy()
links2.drop(['pi','pf'], axis=1, inplace=True)
links2.head()


# In[25]:


# auxiliar para agregar columnas
#links2['id'] = links2.id
#links2['DN'] = [160 for i in range(len(links2))]
#links2['material'] = ['PVC' for i in range(len(links2))]
#links2['CL'] = [6 for i in range(len(links2))]
#links2['int_i'] = [500.1 for i in range(len(links2))]
#links2['tn_i'] = [500.1 for i in range(len(links2))]
#links2['tap_i'] = [1.3 for i in range(len(links2))]
#links2['int_f'] = [500.1 for i in range(len(links2))]
#links2['tn_f'] = [500.1 for i in range(len(links2))]
#links2['tap_f'] = [1.3 for i in range(len(links2))]
#links2['pend_cond'] = [0.001 for i in range(len(links2))]
#links2.head()


# In[26]:


# Exportar shapes para seleccionar salidas invirtiendo tramos.

links2.to_file(nombre_objeto_links2)

nodos_sin_salida.to_file(nombre_objeto_nodos_sin_salida)


# In[27]:


# Punto de pausa para inversión de tramos.

aux = input("¿Continuar? (si/no) ")
if aux != 'si':
    raise Exception


# In[ ]:


# Importación neuvamente de los shapes reemplazando el dataframe links2 que ha quedado redundante.

links2 = geopandas.read_file(nombre_objeto_links2)
links2.to_crs(crs = epsg, inplace = True)
links2.head()


# In[ ]:


# Detalle de links invertidos

links2.loc[links2['invierte'] == 1]


# In[ ]:


# Inversión de nodos

aux = list(links2['ni'])
links2['ni'] = [links2['nf'][i] if links2['invierte'][i] == 1 else links2['ni'][i] for i in range(len(links2))]
links2['nf'] = [aux[i] if links2['invierte'][i] == 1 else links2['nf'][i] for i in range(len(links2))]

aux = list(links2['zi'])
links2['zi'] = [links2['zf'][i] if links2['invierte'][i] == 1 else links2['zi'][i] for i in range(len(links2))]
links2['zf'] = [aux[i] if links2['invierte'][i] == 1 else links2['zf'][i] for i in range(len(links2))]

links2['pend_tn'] = [-links2['pend_tn'][i] if links2['invierte'][i] == 1 else links2['pend_tn'][i] for i in range(len(links2))]

puntos_iniciales2 = geopandas.GeoDataFrame(crs=links2.crs, 
                                          geometry=list(Point(links2.geometry.iloc[i].coords[0]) for i in range(len(links2))))
puntos_finales2 = geopandas.GeoDataFrame(crs=links2.crs, 
                                        geometry=list(Point(links2.geometry.iloc[i].coords[1]) for i in range(len(links2))))

links2['pi'] = [puntos_finales2.geometry[i] if links2['invierte'][i] == 1 
                else puntos_iniciales2.geometry[i] for i in range(len(links2))]
links2['pf'] = [puntos_iniciales2.geometry[i] if links2['invierte'][i] == 1 
                else puntos_finales2.geometry[i] for i in range(len(links2))]

links2.loc[links2['invierte'] == 1]


# In[ ]:


# Modificación de "ventila" con cambios de dirección.

aux = []
for i in range(len(links2)):
    if links2['invierte'][i] == 1:  # Modificar los tramos invertidos
        if links2['ventila'][i] == 1 and len(links2.loc[links2['nf'] == links2['ni'][i]]) > 0:
            aux.append(0)
        else:
            aux.append(1)
    else: # Modificar otros tramos que puedan haber quedado inconexos
        if (len(links2.loc[links2['ni'] == links2['ni'][i]]) == sum(links2['ventila'].loc[links2['ni'] == links2['ni'][i]]) and 
            len(links2.loc[links2['nf'] == links2['ni'][i]]) > 0):
            if links2['pend_tn'][i] != max(links2.loc[links2['ni'] == links2['ni'][i]]['pend_tn']):
                aux.append(1)
            else:
                aux.append(0)   
        else:
            aux.append(links2['ventila'][i])

links2['ventila'] = aux

aux = []
for i in range(len(links2)):
    if (len(links2.loc[links2['ni'] == links2['ni'][i]].loc[links2['ventila'] == 1]) == 
        len(links2.loc[links2['ni'] == links2['ni'][i]]) and 
        len(links2.loc[links2['nf'] == links2['ni'][i]]) > 0): # Si no hay ningún ventila se asigna arbitrariamente al mayor índice
        if i == max(links2.loc[links2['ni'] == links2['ni'][i]].index):
            aux.append(0)
        else:
            aux.append(1)
    else:
        aux.append(links2['ventila'][i])     
links2['ventila'] = aux


# In[ ]:


# Nuevo cálculo de puntos sin salida.

puntos_sin_salida2 = []
for i in range(len(nodos)):
    if i not in pd.unique(links2['ni']):
        puntos_sin_salida2.append(i)
nodos_sin_salida2 = nodos.iloc[puntos_sin_salida2]
nodos_sin_salida2['nodo'] = [nodos_sin_salida2.index[i] for i in range(len(nodos_sin_salida2))]    
nodos_sin_salida2


# In[ ]:


# Nuevo cálculo de longitud acumulada

long_acum2 = [links2['longitud'][i] for i in range(len(links2))]
while sum(long_acum2[i] if links2['nf'][i] in puntos_sin_salida2 
          else 0 for i in range(len(links2))) < sum(links2['longitud']):
    for i in range(len(links2)):
        if links2['ventila'][i] == 0:
            aux = []
            for j in range(len(links2)):
                if links2['nf'][j] == links2['ni'][i]:
                    aux.append(long_acum2[j])
                else:
                    0
            long_acum2[i] = links2['longitud'][i] + sum(aux)
        else:
            continue

links2['long_acum'] = long_acum2
links2.head()


# In[ ]:


# Verificación de longitudes acumuladas paso 1

aux = []
for i in range(len(links2)):
    if links2['nf'][i] in puntos_sin_salida2:
        aux.append(long_acum2[i])
sum(aux)


# In[ ]:


# Verificación de longitudes acumuladas paso 2

sum(links2['longitud'])


# In[ ]:


# Modificación del sentido de los links para que coincidan ni y nf.

links2.set_geometry([LineString([links2['pi'][i], links2['pf'][i]],) for i in range(len(links2))], inplace=True)
links2.head()


# In[ ]:


# Drop de columnas de puntos para evitar conflictos de exportación

links2.drop(['pi', 'pf'], axis=1, inplace=True)
links2.head()


# In[ ]:


# Reseteo de "invierte"

links2['invierte'] = 0


# In[ ]:


# Exportar shapes

links2.to_file(nombre_objeto_links2)
nodos_sin_salida2.to_file(nombre_objeto_nodos_sin_salida)


# In[ ]:


# Punto de pausa para adoptar "ventila" finales

aux = input("¿Continuar? (si/no) ")
if aux != 'si':
    raise Exception


# In[ ]:


# Importar impulsiones

imp = geopandas.read_file(nombre_objeto_impulsiones)
imp.to_crs(crs = epsg, inplace = True)
imp


# In[ ]:


imp['longitud'] = imp.length.round(1)
imp


# In[ ]:


# DataFrames de puntos iniciales y finales.

pts_imp_0 = pd.concat([geopandas.GeoDataFrame(crs=imp.crs, 
                                              geometry=list(Point(imp.geometry.iloc[i].coords[0]) for i in range(len(imp)))), 
                       geopandas.GeoDataFrame(crs=imp.crs, 
                                              geometry=list(Point(imp.geometry.iloc[i].coords[-1]) for i in range(len(imp))))])
                      
pts_imp_0['id_imp'] = pts_imp_0.index
pts_imp_0.set_index(pd.Index([i for i in range(len(pts_imp_0))]), inplace = True)
pts_imp_0


# In[ ]:


# Creación un buffer de 1m de los nodos para identificar vértices iniciales y finales.

distancia = 1
pts_imp_0_buff = pts_imp_0.copy()
pts_imp_0_buff.geometry = pts_imp_0.buffer(distancia)
pts_imp_0_buff.head()


# In[ ]:


# Spatial Join entre puntos sin salida y el buffer de los nodos de la impulsión.

eb = geopandas.sjoin(nodos_sin_salida2, pts_imp_0_buff, how='inner', predicate='intersects')
eb.drop(['index_right'], axis=1, inplace=True)
eb


# In[ ]:


# Determinar longitud acumulada que llega a cada eb

eb['long_acum'] = [sum(links2['long_acum'].loc[links2['nf'] == eb['nodo'].iloc[i]]) for i in range(len(eb))]
eb


# In[ ]:


# Spatial join para obtener los id's de los nodos

descargas = geopandas.sjoin(pts_imp_0[~pts_imp_0.index.isin(eb.id_imp)], nodos_buff, how='inner', predicate='intersects')
descargas.rename(columns = {'index_right':'nodo'}, inplace = True)
descargas


# In[ ]:


# Asignar la longitud acumulada de cada eb a su descarga.
# Esto solo sirve para caudales medios. La impulsión descargará alternadamente el caudal de bombeo.

descargas['long_acum'] = [float(eb['long_acum'].loc[descargas['id_imp'].iloc[i] == eb['id_imp']]) for i in range(len(descargas))]
descargas


# In[ ]:


# Chequeo de ventilas. Que la impulsión no descargue en un nodo en el cual todos ventilen.

# Modificación de longitudes acumuladas que reciben impulsiones

aux = []
for i in range(len(links2)):
    if links2['ni'].isin(descargas['nodo'])[i] == True: # Lista de links cuyo nodo inicial recibe una descarga
        if len(links2.loc[links2['ni'][i] == links2['ni']]) == 1: # Condicional por tramos de inicio únicos que ventilan
            aux.append(links2['longitud'][i] + float(descargas['long_acum'].loc[descargas['nodo'] == links2['ni'][i]]))
        elif links2['ventila'][i] == 0: # Condicional por varios tramos de inicio con solo uno que no ventila
            aux.append(links2['longitud'][i] + float(descargas['long_acum'].loc[descargas['nodo'] == links2['ni'][i]]))
        elif len(links2.loc[links2['ni'][i] == links2['ni']]) == len(links2.loc)
        else:
            aux.append(links2['longitud'][i])
    else:
        aux.append(links2['longitud'][i])
aux

# Nuevo cálculo de longitud acumulada

long_acum2 = [aux[i] for i in range(len(links2))]
while sum(long_acum2[i] if links2['nf'][i] in puntos_sin_salida2 
          else 0 for i in range(len(links2))) < sum(links2['longitud']):
    for i in range(len(links2)):
        if links2['ventila'][i] == 0:
            aux2 = []
            for j in range(len(links2)):
                if links2['nf'][j] == links2['ni'][i]:
                    aux2.append(long_acum2[j])
                else:
                    0
            long_acum2[i] = aux[i] + sum(aux)
        else:
            continue

links2['long_acum'] = long_acum2
links2


# In[ ]:


links2['ni'].isin(descargas['nodo'])[2]


# In[ ]:


# Exportar shapes

links2.to_file(nombre_objeto_links2)


# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:




