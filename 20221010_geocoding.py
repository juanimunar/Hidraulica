#!/usr/bin/env python
# coding: utf-8

# In[1]:


# Bibliotecas

import pandas as pd
import requests


# In[2]:


# Importación de datos desde Excel. Mapa 1

df1 = pd.read_excel(r'C:\Users\Juan Igancio\Desktop\MAPAS\ARCHIVO PARA MAPAS JUANI.xlsx', sheet_name='MAPA 1 OBRAS 2023')
df1.head()


# In[3]:


# Importación de datos desde Excel. Mapa 2

df2 = pd.read_excel(r'C:\Users\Juan Igancio\Desktop\MAPAS\ARCHIVO PARA MAPAS JUANI.xlsx', sheet_name='MAPA 2 ACUMAR 2022')
df2.drop(['Unnamed: 0'], axis=1, inplace=True)
df2.head()


# In[4]:


# Importación de datos desde Excel. Mapa 3

df3 = pd.read_excel(r'C:\Users\Juan Igancio\Desktop\MAPAS\ARCHIVO PARA MAPAS JUANI.xlsx', sheet_name='MAPA 3 ACUMAR 2023')
df3.drop(['Unnamed: 0'], axis=1, inplace=True)
df3.head()


# In[5]:


# Key de la API y función para obtener latitud y longitud de cada dirección

API_KEY = 'AIzaSyDyjTzxdC-nXjNOZA3yWgj4_nyI5xvgdWM'

def coordenadas(dir):
    address = dir
    params = {
        'key': API_KEY,
        'address': address
    }
    base_url = 'https://maps.googleapis.com/maps/api/geocode/json?'
    response = requests.get(base_url, params=params).json()
    
    lat = response['results'][0]['geometry']['location']['lat']
    lng = response['results'][0]['geometry']['location']['lng']
    
    return (lat, lng)    


# In[6]:


df1['coordenadas'] = [coordenadas(df1['DIRECCIÓN'][i]) for i in range(len(df1))]
df1


# In[7]:


df2['coordenadas'] = [coordenadas(df2['DIRECCIÓN CORREGIDA '][i]) for i in range(len(df2))]
df2


# In[8]:


df3['coordenadas'] = [coordenadas(df3['DIRECCIÓN CORREGIDA '][i]) for i in range(len(df3))]
df3


# In[9]:


df1['Y'] = [df1['coordenadas'][i][0] for i in range(len(df1))]
df1['X'] = [df1['coordenadas'][i][1] for i in range(len(df1))]
df2['Y'] = [df2['coordenadas'][i][0] for i in range(len(df2))]
df2['X'] = [df2['coordenadas'][i][1] for i in range(len(df2))]
df3['Y'] = [df3['coordenadas'][i][0] for i in range(len(df3))]
df3['X'] = [df3['coordenadas'][i][1] for i in range(len(df3))]


# In[10]:


# Exportar a Excel porque se jode con geopandas

df1.to_excel(r'C:\Users\Juan Igancio\Desktop\MAPAS\MAPA1.xlsx')
df2.to_excel(r'C:\Users\Juan Igancio\Desktop\MAPAS\MAPA2.xlsx')
df3.to_excel(r'C:\Users\Juan Igancio\Desktop\MAPAS\MAPA3.xlsx')


# In[ ]:




