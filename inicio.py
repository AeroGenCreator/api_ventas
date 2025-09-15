import json
import datetime

import lenguaje
from vender import acceso_a_historial

import streamlit as st
import pandas as pd

l = lenguaje.tu_idioma()
st.title(f':material/store: {l.phrase[0]}')

HOY = datetime.date.today().isoformat()
historial = acceso_a_historial()

def venta_total_de_hoy(data=historial, fecha=HOY):
    try:
        df = pd.DataFrame(data=historial)
        filtro = df[df['Fecha']==HOY]
        total = filtro['Total'].sum()
        return total
    except KeyError:
        return 0

def beneficio_bruto_de_hoy(data=historial,fecha=HOY):
    try:
        df = pd.DataFrame(historial)
        filtro = df[df['Fecha']==HOY]
        filtro['Costo De Bienes'] = filtro['Cantidad'] * filtro['Precio Compra']
        filtro['Beneficio Bruto'] = filtro['Total'] - filtro['Costo De Bienes']
        beneficio_bruto_total = filtro['Beneficio Bruto'].sum()
        return beneficio_bruto_total
    except KeyError:
        return 0
     
def margen_beneficio_bruto_hoy():
    try:
        venta_total = venta_total_de_hoy()
        beneficio_bruto = beneficio_bruto_de_hoy()
        margen = (beneficio_bruto/venta_total) * 100
        return round(margen,2)
    except KeyError:
        return 0

venta = venta_total_de_hoy()
venta = str(venta)
venta = '$ ' + venta

beneficio = beneficio_bruto_de_hoy()
beneficio = str(beneficio)
beneficio = '$ ' + beneficio

margen_beneficio = margen_beneficio_bruto_hoy()
margen_beneficio = str(margen_beneficio)
margen_beneficio = '% ' + margen_beneficio

col_1, col_2 = st.columns([1,3])
col_1.image('pro.jpg',width=95,caption='Bienvenido')
col_2.metric(label='Venta Total Del Dia',value=venta,border=True)

col_3,col_4,col_5 = st.columns(3)

col_4.metric(label='Beneficio Bruto Del Dia',value=beneficio,border=True)
col_5.metric(label='Beneficio Bruto Margen',value=margen_beneficio,border=True)

st.button(label='Corte Del Dia',key='Corte del Dia',width='stretch',type='primary')