import datetime
import json
import os

import lenguaje

import streamlit as st
import pandas as pd

l=lenguaje.tu_idioma()

st.title(f':material/sell: {l.phrase[1]}')

RUTA_HISTORIAL = 'ventas_historial.json'
RUTA_PRODUCTOS = 'catalogo_productos.json'

SALES_EMPTY_DICT = {
    'Folio':[],
    'Fecha':[],
    'Clave SAT':[],
    'Producto Y Modelo':[],
    'Cantidad':[],
    'Unidad':[],
    'Precio':[],
    'Total':[]
    }

CODIGO_QR = 'Cero'

def acceso_a_historial():
    try:
        if os.path.exists(RUTA_HISTORIAL) and os.path.getsize(RUTA_HISTORIAL) > 0:
            with open(RUTA_HISTORIAL,'r',encoding='utf-8') as f:
                data = json.load(f)
                return data
        else:
            with open(RUTA_HISTORIAL, 'w', encoding='utf-8') as f:
                json.dump(SALES_EMPTY_DICT, f, indent=4, ensure_ascii=False)

    except(FileNotFoundError, json.JSONDecodeError, TypeError):
        st.error('Error Al Acceder Al Historial De Ventas')

def get_folio(data:dict):

    df = pd.DataFrame(data=data)

    folio = df['Folio']
    folio = sorted(folio,reverse=True)

    if len(folio) > 0:
        folio = folio[0]
        folio += 1
        return folio
    else:
        return 0

def acceso_a_productos():
    try:
        if os.path.exists(RUTA_PRODUCTOS) and os.path.getsize(RUTA_PRODUCTOS) > 0:
            with open(RUTA_PRODUCTOS, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data
        else:
            st.warning('O El Archivo No Existe O No Hay Datos En El Inventario')
    except(FileNotFoundError):
        st.error('Error Al Acceder Al Historial De Ventas')

def formulario_venta(folio:int, data:dict):

    df=pd.DataFrame(data=data)
    df['Producto Y Modelo']=df['Producto']+df['Dimension']+df['U. Medida']
    df['Precio Venta']=round(df['Precio Venta'])
    df=df.set_index(keys='Producto Y Modelo',drop=True)

    OPCIONES = df.index.to_list()

    DF_VACIO = pd.DataFrame({
        'Cantidad':[None],
        'Producto Y Modelo':[None],
        'Unidad':[None],
        'Clave SAT':[None],
        'Precio':[None],
        'Total':[None],
        'Existencias':[None],
        'Faltas':[None]
    })

    TOTAL_PRODUCTOS = 0
    TOTAL_COSTO = 0

    if 'df' not in st.session_state:
        st.session_state.df = DF_VACIO
    if 'total_productos' not in st.session_state:
        st.session_state.total_productos = TOTAL_PRODUCTOS
    if 'total_costo' not in st.session_state:
        st.session_state.total_costo = TOTAL_COSTO

    hoy = datetime.date.today()

    st.write('Ignacio Picazo Sur No. 30 Santa Ana Chiautempan, Tlaxcala C.P. 90800')

    col_1, col_2, col_3 = st.columns(3)
    col_1.write('__NOTA DE VENTA__')
    col_2.write(f'__No. Folio: :red[{folio}]__')
    col_3.write(hoy)

    df_venta = st.data_editor(
        data=st.session_state.df,
        num_rows='dynamic',
        column_config={
            'Cantidad':st.column_config.NumberColumn(
                width=60,
                help=':orange[Cantidad]',
                required=True,
                pinned=True,
                min_value=1,
                step=1
            ),
            'Producto Y Modelo':st.column_config.SelectboxColumn(
                width=210,
                help=':orange[Producto Y Modelo]',
                required=True,
                pinned=True,
                options=OPCIONES,
                ),
            'Unidad':st.column_config.TextColumn(
                width=60,
                help=':orange[Unidad]',
                disabled=True,
                pinned=True,
            ),
            'Clave SAT':st.column_config.TextColumn(
                width=80,
                help=':orange[Clave SAT]',
                disabled=True,
                pinned=True
            ),
            'Precio':st.column_config.NumberColumn(
                width=70,
                help=':orange[Precio]',
                disabled=True,
                pinned=True,
                format='dollar',
            ),
            'Total':st.column_config.NumberColumn(
                width=70,
                help=':orange[Total]',
                disabled=True,
                pinned=True,
                format='dollar'
            ),
            'Existencias':st.column_config.NumberColumn(
                width=70,
                help=':orange[Existencias]',
                disabled=True,
                pinned=True,
            ),
            'Faltas':st.column_config.TextColumn(
                width=50,
                help=':orange[Faltas]',
                disabled=True,
                pinned=True,
            )
        }
    )

    df_venta = pd.DataFrame(data=df_venta)

    if df_venta.empty:
        st.session_state.df=DF_VACIO
        st.session_state.total_productos=TOTAL_PRODUCTOS
        st.session_state.total_costo=TOTAL_COSTO

    col_4, col_5 = st.columns(2)
    col_4.metric(
        label='Total De Productos',
        value=TOTAL_PRODUCTOS,
        help=':orange[Este Calculo Se Realiza Automatico Despues De Calcular Totales]',
        border=True,
        height='stretch'
        )
    col_5.metric(
        'Total De Costo',
        value=TOTAL_COSTO,
        help=':orange[Este Calculo Se Realiza Automatico Despues De Calcular Totales]',
        border=True,
        height='stretch'
        )

    col_6, col_7, col_8, = st.columns(3)
    with col_6:
        calculo = st.button(
            label='Calcular Totales',
            key='calcular_totales',
            type='secondary',
            help=':orange[Requiere Doble Click]',
            width='stretch'
        )
    with col_7:
        limpiar_tabla = st.button(
            label='Limpiar - Cargar Cache',
            key='reset_tabla',
            type='secondary',
            help=':orange[Requiere Doble Click]',
            width='stretch'
            )
    with col_8:
        registar_venta = st.button(
            label='Registrar Venta',
            key='registrar_venta',
            type='primary',
            help=':orange[Requiere Doble Click]',
            width='stretch'
        )

    if calculo:
        df_venta=df_venta.dropna(axis=0,how='any',subset=['Cantidad','Producto Y Modelo'])
        df_venta=df_venta.drop_duplicates(subset=['Producto Y Modelo'],keep='first',ignore_index=True)
        st.session_state.df=df_venta

    if limpiar_tabla:
        try:
            st.session_state.df=DF_VACIO
            st.session_state.total_productos = TOTAL_PRODUCTOS
            st.session_state.total_costo = TOTAL_COSTO
        except KeyError:
            if 'df' not in st.session_state:
                st.session_state.df = DF_VACIO
            if 'total_productos' not in st.session_state:
                st.session_state.total_productos = TOTAL_PRODUCTOS
            if 'total_costo' not in st.session_state:
                st.session_state.total_costo = TOTAL_COSTO


# LLAMADO A LAS FUNCIONES ----------------------------------------------------------------------

historial = acceso_a_historial()
folio = get_folio(historial)
productos = acceso_a_productos()
formulario_venta(folio=folio,data=productos)
st.dataframe(historial)