#!/usr/bin/env python
# coding: utf-8

# In[1]:


# Importar librerías.

import pandas as pd
import numpy as np
import geopandas
import rasterio
from shapely.geometry import Point, LineString


# In[2]:


# Ubicación de shapes

# Cuencas
nombre_objeto_cuencas = r'C:\Users\Juan Igancio\Desktop\Pluviales\O2023_GIS\SHP\O2023B_CUENCAS_3857_20230104_NB.shp'

# Trayectorias hidráulicas
nombre_objeto_th = r'C:\Users\Juan Igancio\Desktop\Pluviales\O2023_GIS\SHP\O2023B_TRAYECTORIA_3857_20230104_NB.shp'

# Sumideros
nombre_objeto_sumideros = r'C:\Users\Juan Igancio\Desktop\Pluviales\O2023_GIS\SHP\O2023B_SUMIDEROS_3857_20230104_NB.shp'

# Nexos
nombre_objeto_nexos = r'C:\Users\Juan Igancio\Desktop\Pluviales\O2023_GIS\SHP\O2023B_NEXOS_3857_20230104_NB.shp'

# BR
nombre_objeto_br = r'C:\Users\Juan Igancio\Desktop\Pluviales\O2023_GIS\SHP\O2023B_BR_3857_20230104_NB.shp'

# Conductos originales
nombre_objeto_conductos = r'C:\Users\Juan Igancio\Desktop\Pluviales\O2023_GIS\SHP\O2023B_CONDUCTOS_3857_20230104_NB.shp'

# DEM en formato raster, se debe importar en el mismo SRC con el que se va a trabajar, deuda pendiente
nombre_objeto_dem = r'C:\Users\Juan Igancio\Desktop\Pluviales\O2023_GIS\RASTER\DEM_5348.tif'

# Cuencas salida
nombre_objeto_cuencas_s = r'C:\Users\Juan Igancio\Desktop\Pluviales\O2023_GIS\SHP\O2023B_CUENCAS_3857_20230104_S.shp'

# Trayectorias hidráulicas salida
nombre_objeto_th_s = r'C:\Users\Juan Igancio\Desktop\Pluviales\O2023_GIS\SHP\O2023B_TRAYECTORIA_3857_20230104_S.shp'

# Sumideros salida
nombre_objeto_sumideros_s = r'C:\Users\Juan Igancio\Desktop\Pluviales\O2023_GIS\SHP\O2023B_SUMIDEROS_3857_20230104_S.shp'

# Nexos salida
nombre_objeto_nexos_s = r'C:\Users\Juan Igancio\Desktop\Pluviales\O2023_GIS\SHP\O2023B_NEXOS_3857_20230104_S.shp'

# BR salida
nombre_objeto_br_s = r'C:\Users\Juan Igancio\Desktop\Pluviales\O2023_GIS\SHP\O2023B_BR_3857_20230104_S.shp'

# Conductos originales salida
nombre_objeto_conductos_s = r'C:\Users\Juan Igancio\Desktop\Pluviales\O2023_GIS\SHP\O2023B_CONDUCTOS_3857_20230104_S.shp'


# In[3]:


# Sistema de coordenadas de referencia a partir de su número EPSG.

epsg = 5348


# In[4]:


# Importar shape de cuencas y cálculo de áreas [ha].

cuencas = geopandas.read_file(nombre_objeto_cuencas)
cuencas.to_crs(crs = epsg, inplace = True)
cuencas['id_cuenca'] = cuencas.index
cuencas = cuencas[['id_cuenca','geometry']]
cuencas['area'] = cuencas.area.round(0)/10000
cuencas.head()


# In[5]:


# Importar DEM

dem = rasterio.open(nombre_objeto_dem)


# In[6]:


# Importar shape de sumideros

sumideros = geopandas.read_file(nombre_objeto_sumideros)
sumideros.to_crs(crs = epsg, inplace = True)
sumideros['id_sumidero'] = sumideros.index
sumideros = sumideros[['id_sumidero','geometry']]
sumideros.head()


# In[7]:


# Obtener coordenadas CTN de sumideros

sumideros['CTN'] = [round(float(i),2) for i in 
                  dem.sample([(x,y) for x,y in zip(sumideros['geometry'].x , sumideros['geometry'].y)])]
sumideros.head()


# In[8]:


# Importar trayectorias hidráulicas y cálculo de longitudes

th = geopandas.read_file(nombre_objeto_th)
th.to_crs(crs = epsg, inplace = True)
th['id_th'] = th.index
th = th[['id_th', 'geometry']]
th['longitud'] = th.length.round(1)
th.head()


# In[9]:


# Obtención de cotas de la trayectoria hidráulica y cálculo de pendiente

th['CTNi'] = [round(float(i),2) for i in dem.sample([(x,y) for x,y in zip(
    geopandas.GeoDataFrame(crs=th.crs, geometry=list(Point(th.geometry.iloc[i].coords[0]) 
                                                     for i in range(len(th))))['geometry'].x , 
    geopandas.GeoDataFrame(crs=th.crs, geometry=list(Point(th.geometry.iloc[i].coords[0]) 
                                                     for i in range(len(th))))['geometry'].y)])]
th['CTNf'] = [round(float(i),2) for i in dem.sample([(x,y) for x,y in zip(
    geopandas.GeoDataFrame(crs=th.crs, geometry=list(Point(th.geometry.iloc[i].coords[1]) 
                                                     for i in range(len(th))))['geometry'].x , 
    geopandas.GeoDataFrame(crs=th.crs, geometry=list(Point(th.geometry.iloc[i].coords[1]) 
                                                     for i in range(len(th))))['geometry'].y)])]
th['i_TN'] = (th['CTNi']-th['CTNf'])/th['longitud']

# Nota, por cuestión de urgencia se toma el valor absoluto de la pendiente sin tener en cuenta posibles errores en el trazado.
# Se deben independizar los errores a futuro obteniendo el nodo final de la th a partir de la union espacial con los sumideros.

th['i_adop'] = [0.0005 if abs(th['i_TN'].iloc[i]) <= 0.0005 else abs(th['i_TN'].iloc[i]) for i in range(len(th))]
th.head()


# In[10]:


# Cálculo del tiempo de concentración, establecer el tiempo de mojado "t_mojado" en minutos.

t_mojado = 5
th['tc'] = [t_mojado + round(th['longitud'].iloc[i]/(8.8*60*th['i_adop'].iloc[i]**0.5),1) for i in range(len(th))]
th.head()


# In[11]:


# Uniones espaciales entre sumideros, cuencas y trayectorias hidráulicas.

sumideros_m = sumideros.sjoin_nearest(th, how='left')
sumideros_m.drop(['index_right'], axis=1, inplace=True)
sumideros_m = sumideros_m.sjoin(cuencas, how='left')
sumideros_m.drop(['longitud','CTNi','CTNf','i_TN','i_adop','index_right'], axis=1, inplace=True)
sumideros_m.head()


# In[12]:


# Dimensionado de sumideros, caudales en m³/s

C = 0.8
sumideros_m['I_10'] = [int(584.43*sumideros_m['tc'].iloc[i]**-.611) for i in range(len(sumideros_m))]
sumideros_m['Q_10'] = round(C * sumideros_m['I_10'] * sumideros_m['area'] / 360, 2)
sumideros_m['I_5'] = [int(514.81*sumideros_m['tc'].iloc[i]**-.611) for i in range(len(sumideros_m))]
sumideros_m['Q_5'] = round(C * sumideros_m['I_5'] * sumideros_m['area'] / 360, 2)
sumideros_m['I_2'] = [int(435.3*sumideros_m['tc'].iloc[i]**-.611) for i in range(len(sumideros_m))]
sumideros_m['Q_2'] = round(C * sumideros_m['I_2'] * sumideros_m['area'] / 360, 2)

# Capacidad de sumideros 100 l/m (1 cuerpo)

cap_sum = 100

sumideros_m['n_cuerpos'] = round(sumideros_m['Q_10']/cap_sum*1000,0)

sumideros_m.head()


# In[13]:


# Importar nexos

nexos = geopandas.read_file(nombre_objeto_nexos)
nexos.to_crs(crs = epsg, inplace = True)
nexos['id_nexo'] = nexos.index
nexos = nexos[['id_nexo', 'geometry']]
nexos['longitud'] = nexos.length.round(1)
nexos.head()


# In[14]:


# Determinar cotas y pendiente del nexo. NOTA: nuevamente se adopta valor absoluto por disponibilidad de tiempo

nexos['CTNi'] = [round(float(i),2) for i in dem.sample([(x,y) for x,y in zip(
    geopandas.GeoDataFrame(crs=nexos.crs, geometry=list(Point(nexos.geometry.iloc[i].coords[0]) 
                                                     for i in range(len(nexos))))['geometry'].x , 
    geopandas.GeoDataFrame(crs=nexos.crs, geometry=list(Point(nexos.geometry.iloc[i].coords[0]) 
                                                     for i in range(len(nexos))))['geometry'].y)])]
nexos['CTNf'] = [round(float(i),2) for i in dem.sample([(x,y) for x,y in zip(
    geopandas.GeoDataFrame(crs=nexos.crs, geometry=list(Point(nexos.geometry.iloc[i].coords[1]) 
                                                     for i in range(len(nexos))))['geometry'].x , 
    geopandas.GeoDataFrame(crs=nexos.crs, geometry=list(Point(nexos.geometry.iloc[i].coords[1]) 
                                                     for i in range(len(nexos))))['geometry'].y)])]
tapada_i = 0.8
tapada_f = 1.2

nexos['i'] = abs((nexos['CTNi']-tapada_i)-(nexos['CTNf']-tapada_f))/nexos['longitud']
nexos.head()


# In[15]:


# Unión espacial de nexos y sumideros

nexos_m = nexos.sjoin_nearest(sumideros_m, how='left')
nexos_m.drop(['index_right', 'n_cuerpos', 'I_10', 'I_5', 'I_2','CTN'], axis=1, inplace=True)
nexos_m.head()


# In[16]:


# Dimensionado de nexos

n = 0.012
nexos_m['D_10'] = round((nexos_m['Q_10']*n/nexos_m['i']**0.5*4**(5/3)/np.pi)**(3/8),2)
nexos_m['D_5'] = round((nexos_m['Q_5']*n/nexos_m['i']**0.5*4**(5/3)/np.pi)**(3/8),2)
nexos_m['D_2'] = round((nexos_m['Q_2']*n/nexos_m['i']**0.5*4**(5/3)/np.pi)**(3/8),2)
nexos_m['D'] = [round(nexos_m['D_10'].iloc[i],1)*1000 if round(nexos_m['D_10'].iloc[i],1)*1000>=400 else 400 for i in range(len(nexos_m))]
nexos_m['V'] = round(nexos_m['Q_10']/(np.pi/4*(nexos_m['D']/1000)**2),1)
nexos_m['tv_tc'] = round(nexos_m['longitud']/nexos_m['V']/60,1) + nexos_m['tc']
nexos_m.head()


# In[17]:


# Importar conductos

conductos = geopandas.read_file(nombre_objeto_conductos)
conductos.to_crs(crs = epsg, inplace = True)
conductos['id_conducto'] = conductos.index
conductos = conductos[['id_conducto','geometry']]
conductos['longitud'] = conductos.length.round(1)
conductos.head()


# In[18]:


# Obtención de cotas del TN de conductos. Por cuestion de tiempo no se invierten tramos automaticamente

conductos['CTNi'] = [round(float(i),2) for i in dem.sample([(x,y) for x,y in zip(
    geopandas.GeoDataFrame(crs=conductos.crs, geometry=list(Point(conductos.geometry.iloc[i].coords[0]) 
                                                     for i in range(len(conductos))))['geometry'].x , 
    geopandas.GeoDataFrame(crs=conductos.crs, geometry=list(Point(conductos.geometry.iloc[i].coords[0]) 
                                                     for i in range(len(conductos))))['geometry'].y)])]
conductos['CTNf'] = [round(float(i),2) for i in dem.sample([(x,y) for x,y in zip(
    geopandas.GeoDataFrame(crs=conductos.crs, geometry=list(Point(conductos.geometry.iloc[i].coords[1]) 
                                                     for i in range(len(conductos))))['geometry'].x , 
    geopandas.GeoDataFrame(crs=conductos.crs, geometry=list(Point(conductos.geometry.iloc[i].coords[1]) 
                                                     for i in range(len(conductos))))['geometry'].y)])]
conductos['i'] = (conductos['CTNi']-conductos['CTNf'])/conductos['longitud']
conductos['i_conducto'] = [max(conductos['i'][j],0.003) for j in range(len(conductos))]
conductos.head()


# In[19]:


# Conductos con pendiente negativa del TN

conductos.loc[conductos['i'] < 0]


# In[20]:


# Importación de BR

br = geopandas.read_file(nombre_objeto_br)
br.to_crs(crs = epsg, inplace = True)
br['id_br'] = br.index
br = br[['id_br','geometry']]
br.head()


# In[21]:


# Unión espacial de nexos con BR

nexos_br = nexos_m[['area','geometry','tv_tc']].sjoin_nearest(br, how='left')
nexos_br.head()


# In[22]:


br['area_br'] = [sum(nexos_br['area'].loc[nexos_br['id_br'] == br['id_br'][i]]) for i in range(len(br))]
br.head()


# In[23]:


# Tiempos de concentración para cada BR

br['tv_tc'] = [max(nexos_br['tv_tc'].loc[nexos_br['id_br'] == br['id_br'][i]]) if 
               sum(nexos_br['tv_tc'].loc[nexos_br['id_br'] == br['id_br'][i]])>0  else 0 for i in range(len(br))]
br.head()


# In[24]:


# Puntos iniciales y puntos finales de conducto

puntos_iniciales = geopandas.GeoDataFrame(crs=conductos.crs, 
                                          geometry=list(Point(conductos.geometry.iloc[i].coords[0]) for i in range(len(conductos))))
puntos_finales = geopandas.GeoDataFrame(crs=conductos.crs, 
                                        geometry=list(Point(conductos.geometry.iloc[i].coords[1]) for i in range(len(conductos))))
puntos_iniciales.head()


# In[25]:


# Identificación con BR

conductos['br_inicial'] = puntos_iniciales.sjoin_nearest(br, how='left')['id_br']
conductos['area_br'] = puntos_iniciales.sjoin_nearest(br, how='left')['area_br']
conductos['tv_tc'] = puntos_iniciales.sjoin_nearest(br, how='left')['tv_tc']
conductos['br_final'] = puntos_finales.sjoin_nearest(br, how='left')['id_br']
conductos.head()


# In[26]:


# Matriz de aportes

mat_apo = pd.DataFrame(index = [i for i in range(len(conductos))], columns = [i for i in range(len(conductos))], data = 0)
for i in range(len(conductos)):
    mat_apo[i] = conductos.index.isin(pd.Series(conductos.index).loc[conductos['br_final'] == conductos['br_inicial'][i]])*1
mat_apo.iloc[:7,:7]


# In[27]:


# Por simplicidad se itera una cantidad de veces igual a la cantidad de tramos existentes.

k = 0
for k in range(len(conductos)):
    for i in range(len(conductos)):
        for j in range(len(conductos)):
            if mat_apo[i][j] == 1:
                mat_apo[i] = mat_apo[i] + mat_apo[j]
                mat_apo = (mat_apo/mat_apo).fillna(0)
mat_apo.iloc[:7,:7]       


# In[28]:


# Se completa la matriz de aporte con el aporte propio de cada tramo

for i in range(len(conductos)):
    mat_apo[i][i] = 1
mat_apo.iloc[:7,:7]


# In[29]:


# Matriz de aporte tv_tc

mat_apo_tv_tc = mat_apo.copy()
for i in range(len(conductos)):
    for j in range(len(conductos)):
        mat_apo_tv_tc[i][j] = mat_apo[i][j]*conductos['tv_tc'][j]
mat_apo_tv_tc


# In[30]:


# Matriz de aporte de áreas

mat_apo_area = mat_apo.copy()
for i in range(len(conductos)):
    for j in range(len(conductos)):
        mat_apo_area[i][j] = mat_apo[i][j]*conductos['area_br'][j]
mat_apo_area.head()


# In[31]:


# Cálculo del área acumulada

conductos['area_acum'] = [sum(mat_apo_area[i]) for i in range(len(conductos))]
conductos.head()


# In[32]:


# Matriz para el cálculo de tiempos de viaje

mat_apo_0 = pd.DataFrame(index = [i for i in range(len(conductos))], columns = [i for i in range(len(conductos))], data = 0)
for i in range(len(conductos)):
    mat_apo_0[i] = conductos.index.isin(pd.Series(conductos.index).loc[conductos['br_final'] == conductos['br_inicial'][i]])*1
k = 0
for k in range(len(conductos)):
    for i in range(len(conductos)):
        for j in range(len(conductos)):
            if mat_apo_0[i][j] == 1:
                mat_apo_0[i] = mat_apo_0[i] + mat_apo_0[j]
                mat_apo_0 = (mat_apo_0/mat_apo_0).fillna(0)
                
conductos['tv'] = conductos['longitud']/1.5/60
tv_mat_apo = mat_apo_0*conductos['tv']
tv_mat_apo


# In[33]:


# Determinación del tiempo de concentración

tv = [sum([tv_mat_apo[i][j] for j in range(len(conductos))]) for i in range(len(conductos))]
tv_tc = [max([mat_apo_tv_tc[i][j] for j in range(len(conductos))]) for i in range(len(conductos))]
tv_tc
conductos['tc'] = [tv[i]+tv_tc[i] for i in range(len(conductos))]
conductos.head()


# In[34]:


conductos


# In[35]:


# Predimensionado

C = 0.8
conductos['I_10'] = [int(584.43*conductos['tc'].iloc[i]**-.611) for i in range(len(conductos))]
conductos['Q_10'] = round(C * conductos['I_10'] * conductos['area_acum'] / 360, 2)
conductos['I_5'] = [int(514.81*conductos['tc'].iloc[i]**-.611) for i in range(len(conductos))]
conductos['Q_5'] = round(C * conductos['I_5'] * conductos['area_acum'] / 360, 2)
conductos['I_2'] = [int(435.3*conductos['tc'].iloc[i]**-.611) for i in range(len(conductos))]
conductos['Q_2'] = round(C * conductos['I_2'] * conductos['area_acum'] / 360, 2)

n = 0.012
conductos['D_10'] = round((conductos['Q_10']*n/conductos['i_conducto']**0.5*4**(5/3)/np.pi)**(3/8),2)
conductos['D_5'] = round((conductos['Q_5']*n/conductos['i_conducto']**0.5*4**(5/3)/np.pi)**(3/8),2)
conductos['D_2'] = round((conductos['Q_2']*n/conductos['i_conducto']**0.5*4**(5/3)/np.pi)**(3/8),2)
conductos['D_prov'] = [round(conductos['D_10'].iloc[i],1)*1000 if round(conductos['D_10'].iloc[i],1)*1000>=400 else 400 for i in range(len(conductos))]
conductos.head()


# In[36]:


# Matriz de diámetros

mat_apo_d = mat_apo.copy()
for i in range(len(conductos)):
    for j in range(len(conductos)):
        mat_apo_d[i][j] = mat_apo[i][j]*conductos['D_prov'][j]
mat_apo_d.head()


# In[37]:


# Corrección de diámetros

conductos['D'] = [max([mat_apo_d[i][j] for j in range(len(conductos))]) for i in range(len(conductos))]
conductos.head()


# In[38]:


# Importar nombre de obras

nombre_objeto_obras = r'C:\Users\Juan Igancio\Desktop\Pluviales\O2023_GIS\SHP\OBRAS.shp'
obras = geopandas.read_file(nombre_objeto_obras)
obras.to_crs(crs = epsg, inplace = True)
obras.head()    


# In[39]:


# Bautizando shapes

cuencas = cuencas.sjoin(obras, how='left')
cuencas.drop(['index_right'], axis=1, inplace=True)
th = th.sjoin(obras, how='left')
th.drop(['index_right'], axis=1, inplace=True)
sumideros_m = sumideros_m.sjoin(obras, how='left')
sumideros_m.drop(['index_right'], axis=1, inplace=True)
sumideros_m
nexos_m = nexos_m.sjoin(obras, how='left')
nexos_m.drop(['index_right'], axis=1, inplace=True)
br = br.sjoin(obras, how='left')
br.drop(['index_right'], axis=1, inplace=True)
conductos = conductos.sjoin(obras, how='left')
conductos.drop(['index_right'], axis=1, inplace=True)


# In[40]:


# Cuencas salida
cuencas.to_file(nombre_objeto_cuencas_s)

# Trayectorias hidráulicas salida
th.to_file(nombre_objeto_th_s)

# Sumideros salida
sumideros_m.to_file(nombre_objeto_sumideros_s)

# Nexos salida
nexos_m.to_file(nombre_objeto_nexos_s)

# BR salida
br.to_file(nombre_objeto_br_s)

# Conductos originales salida
conductos.to_file(nombre_objeto_conductos_s)


# In[ ]:




