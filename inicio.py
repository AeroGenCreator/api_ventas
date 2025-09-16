import json
import datetime

from config import acceso_fondo_caja
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

def total_productos_del_dia(data=historial,fecha=HOY):
    try:
        df = pd.DataFrame(data=historial)
        filtro = df[df['Fecha']==HOY]
        productos_total = filtro['Cantidad'].sum()
        return productos_total
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

fondo = acceso_fondo_caja()
fondo = str(fondo)
fondo = '$ ' + fondo

caja = acceso_fondo_caja()
extra = venta_total_de_hoy()
total_en_caja = extra + caja
total_en_caja = str(total_en_caja)
total_en_caja = '$ ' + total_en_caja

tab_1, tab_2 = st.tabs(['Inicio','Corte'])

with tab_1:
    col_1, col_2 = st.columns([1,3])

    col_1.image('pro.jpg',width=95,caption='Providencia')
    col_2.metric(label='Venta Total Del Dia',value=venta,border=True)

    col_3,col_4,col_5 = st.columns(3)

    col_3.metric(label='Total De Productos Vendidos',value=total_productos_del_dia(),border=True)
    col_4.metric(label='Beneficio Bruto Del Dia',value=beneficio,border=True)
    col_5.metric(label='Beneficio Bruto Margen',value=margen_beneficio,border=True)

    col_6, col_7 = st.columns(2)
    col_6.metric(label='Fondo de Caja', value=fondo, border=True,width='stretch')
    col_7.metric(label='Total En Caja', value=total_en_caja, border=True,width='stretch')

with tab_2:
    st.markdown(f'Total Caja: {total_en_caja}')
    st.markdown(f'Venta Total: {venta}')
    st.markdown(f'Fondo Caja: {fondo}')

    st.button(label='Corte Del Dia',key='Corte del Dia',width='stretch',type='primary')