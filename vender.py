import datetime
import json
import os

import lenguaje

import streamlit as st
import pandas as pd
from escpos.printer import Usb
from fpdf import FPDF

l=lenguaje.tu_idioma()

st.header(f':material/sell: {l.phrase[1]}')

DIRECCION = 'Santa Ana Chiautempan, Tlaxcala C.P. 90800'

RUTA_HISTORIAL = 'ventas_historial.json'
RUTA_PRODUCTOS = '_inventario_providencia.json'

CODIGO_QR = 'Cero'

def acceso_a_historial():
    try:
        if os.path.exists(RUTA_HISTORIAL) and os.path.getsize(RUTA_HISTORIAL) > 0:
            with open(RUTA_HISTORIAL,'r',encoding='utf-8') as f:
                data = json.load(f)
                return data
        else:
            st.warning('Realiza Una Venta Para Comenzar Almacenamiento de Registros')

    except(FileNotFoundError, json.JSONDecodeError, TypeError):
        st.error('Error Al Acceder Al Historial De Ventas')

def get_folio(data:dict):
    try:
        df = pd.DataFrame(data=data)

        folio = df['Folio']
        folio = sorted(folio,reverse=True)

        if len(folio) > 0:
            folio = folio[0]
            folio += 1
            return folio
        else:
            return 0
    except KeyError:
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
    df['Indice P'] = df['Producto']
    copia1 = df.copy()
    copia1['Precio Lista']=round(copia1['Precio Lista'])
    copia2 = df.copy()
    
    df.set_index(keys='Indice P',inplace=True)
    copia1.set_index(keys='Producto',inplace=True)
    copia2.set_index(keys='Producto',inplace=True)

    OPCIONES = copia1.index.to_list()

    DF_VACIO = pd.DataFrame({
        'Piezas':[None],
        'Producto':[None],
        'C 1':[None],
        'C 2':[None],
        'U. Medida':[None],
        'Precio':[None],
        'Total':[None],
        'Existencias':[None]
    })

    TOTAL_PRODUCTOS = 0
    TOTAL_COSTO = 0

    if 'df' not in st.session_state:
        st.session_state.df = DF_VACIO
    if 'total_productos' not in st.session_state:
        st.session_state.total_productos = TOTAL_PRODUCTOS
    if 'total_costo' not in st.session_state:
        st.session_state.total_costo = TOTAL_COSTO

    HOY = datetime.date.today()

    st.write(DIRECCION)

    col_1, col_2, col_3 = st.columns(3)
    col_1.write('__NOTA DE VENTA__')
    col_2.write(f'__No. Folio: :red[{folio}]__')
    col_3.write(HOY)

    df_venta = st.data_editor(
        data=st.session_state.df,
        num_rows='dynamic',
        column_config={
            'Piezas':st.column_config.NumberColumn(
                width=75,
                help=':orange[Piezas]',
                required=True,
                pinned=True,
                min_value=1,
                step=1
            ),
            'Producto':st.column_config.SelectboxColumn(
                width=180,
                help=':orange[Producto]',
                required=True,
                pinned=True,
                options=OPCIONES,
                ),
            'C 1':st.column_config.TextColumn(
                width=60,
                help=':orange[Categoría 1]',
                disabled=True,
                pinned=True,
            ),
            'C 2':st.column_config.TextColumn(
                width=75,
                help=':orange[Categoría 2]',
                disabled=True,
                pinned=True
            ),
            'U. Medida':st.column_config.TextColumn(
                width=70,
                help=':orange[Unidad]',
                disabled=True,
                pinned=True,
            ),
            'Precio':st.column_config.NumberColumn(
                width=80,
                help=':orange[Precio]',
                disabled=True,
                pinned=True,
                format='dollar'
            ),
            'Total':st.column_config.NumberColumn(
                width=80,
                help=':orange[Total]',
                format='dollar',
                disabled=True,
                pinned=True,
            ),
            'Existencias':st.column_config.NumberColumn(
                width=60,
                help=':orange[Existencias]',
                disabled=True,
                pinned=True,
            )
        }
    )

    df_venta = pd.DataFrame(data=df_venta)

    if df_venta.empty:
        try:
            st.session_state.df=DF_VACIO
            st.session_state.total_productos=TOTAL_PRODUCTOS
            st.session_state.total_costo=TOTAL_COSTO
        except KeyError:
            if 'df' not in st.session_state:
                st.session_state.df =DF_VACIO
            if 'total_productos' not in st.session_state:
                st.session_state.total_productos=TOTAL_PRODUCTOS
            if 'total_costo' not in st.session_state:
                st.session_state.total_costo=TOTAL_COSTO

    col_4, col_5 = st.columns(2)
    col_4.metric(
        label='Total De Productos',
        value=st.session_state.total_productos,
        help=':orange[Este Calculo Se Realiza Automatico Despues De Calcular Totales]',
        border=True,
        height='stretch',
        )
    col_5.metric(
        'Total De Costo',
        value=st.session_state.total_costo,
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
        registrar_venta = st.button(
            label='Registrar Venta',
            key='registrar_venta',
            type='primary',
            help=':orange[Requiere Doble Click]',
            width='stretch'
        )

    if calculo or registrar_venta:

        df_venta=df_venta.dropna(axis=0,how='any',subset=['Piezas','Producto'])
        df_venta=df_venta.drop_duplicates(subset=['Producto'],keep='first',ignore_index=True)

        copia1 = copia1.loc[df_venta['Producto'],:]

        df_union = df_venta.merge(copia1,how='left', on='Producto')

        df_union['C 1'] = df_union['Categoría 1']
        df_union['C 2'] = df_union['Categoría 2']
        df_union['U. Medida'] = df_union['Unidad']
        df_union['Precio'] = df_union['Precio Lista']
        df_union['Total'] = df_union['Piezas'] * df_union['Precio Lista']
        df_union['Existencias'] = df_union['Cantidad']

        df_union = df_union[[
            'Piezas',
            'Producto',
            'C 1',
            'C 2',
            'U. Medida',
            'Precio',
            'Total',
            'Existencias'
        ]]

        st.session_state.df=df_union
        st.session_state.total_productos = df_union['Piezas'].sum()
        st.session_state.total_costo = df_union['Total'].sum()

        if registrar_venta:
            
            df_salida = st.session_state.df
            productos_vendidos = st.session_state.total_productos
            costos_totales = st.session_state.total_costo
            
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
            
            # Filtro los articulos que no pueden ser vendidos por falta de inventario y aquellos de los cuales no se tenga inventario.
            df_salida['Mascara'] = (df_salida['Existencias'] - df_salida['Piezas']) < 0

            if df_salida['Mascara'].any():
                st.warning('No Se Puede Realizar La Venta, Posiblemente No Hay Inventario Para La Cantidad Deseada')
                st.info('La Tabla Se Limpiara Nuevamente, Puedes Hacerlo Manualmente Si Prefieres')
                return
            
            df_salida.drop(inplace=True,labels='Mascara',axis=1)
            
            copia2 = copia2.loc[df_salida['Producto'],:]
            
            df_ajuste = df_salida.merge(copia2,how='left',on='Producto')
            df_ajuste['Cantidad'] = df_ajuste['Cantidad'] - df_ajuste['Piezas']
            df_ajuste = df_ajuste[[
                'Codigo',
                'Producto',
                'Cantidad',
                'Categoría 1',
                'Categoría 2',
                'Unidad',
                'Precio Compra',
                'Porcentaje Ganancia',
                'Precio Lista',
                'Clave',
                'Oficial'
                ]]
            
            df.loc[df_ajuste['Producto']]=df_ajuste.values
            df.reset_index(drop=True, inplace=True)
            datos = df.to_dict(orient='list')
            
            df_ajuste['Folio'] = folio
            df_ajuste['Fecha'] = HOY.isoformat()
            df_ajuste['Cantidad'] = df_salida['Piezas']
            df_ajuste['Total'] = df_salida['Piezas'] * df_salida['Precio']
            df_ajuste = df_ajuste[[
                'Folio',
                'Fecha',
                'Codigo',
                'Producto',
                'Cantidad',
                'Categoría 1',
                'Categoría 2',
                'Unidad',
                'Precio Compra',
                'Porcentaje Ganancia',
                'Precio Lista',
                'Total',
                'Clave',
                'Oficial'
            ]]

            with open(RUTA_PRODUCTOS,'w',encoding='utf-8') as f:
                json.dump(datos,f,indent=4,ensure_ascii=False)

            if os.path.exists(RUTA_HISTORIAL) and os.path.getsize(RUTA_HISTORIAL) > 0:
                historial_actual = acceso_a_historial()
                df_historial = pd.DataFrame(data=historial_actual)
                datos_historial = pd.concat([df_historial,df_ajuste])
                datos_historial = datos_historial.to_dict(orient='list')
                with open(RUTA_HISTORIAL,'w',encoding='utf-8') as h:
                    json.dump(datos_historial,h,indent=4,ensure_ascii=False)
            else:
                with open(RUTA_HISTORIAL,'w',encoding='utf-8') as h:
                    datos_nuevos = df_ajuste.to_dict(orient='list')
                    json.dump(datos_nuevos,h,indent=4,ensure_ascii=False)

            st.success('Venta Registrada')

            # Aqui comienza el codigo que genera la nota impresa como hoja tamanho carta pdf:
            class PDF(FPDF):
                def __init__(self, orientation = "portrait", unit = "mm", format = "letter"):
                    super().__init__(orientation, unit, format)
                    self.add_font(family='ArialUnicodeMS',fname='arial-unicode-ms.ttf',uni=True)
                def header(self):
                    self.set_text_color(0,0,0)
                    self.set_font(family='ArialUnicodeMS',size=20)
                    self.image('pro.jpg',10,8,16)
                    self.cell(20,6,txt='Ticket De Venta',border=False,center=True,ln=True,align='C')
                    self.ln(15)
                    return super().header()
                def footer(self):
                    self.set_y(-10)
                    self.set_font(family='ArialUnicodeMS',size=7)
                    self.cell(0,6,txt=f'Pagina {self.page_no()}/{{nb}}',center=True)
                    return super().footer()

            pdf = PDF()
            # Salto de pagina automatico
            pdf.set_auto_page_break(auto=True,margin=10)

            # Parametros para la hoja PDF
            pdf.add_page()
            pdf.set_font(family='ArialUnicodeMS',size=9)
            pdf.set_line_width(0.1)
            pdf.set_draw_color(224,224,224)
            pdf.set_fill_color(224,224,224)#204,255,229
            pdf.set_text_color(96,96,96)

            # Datos Extras:
            pdf.cell(98,6,txt=f'Direccion: {DIRECCION}',border=True,align='C')
            pdf.cell(49,6,txt=f'Fecha: {HOY.isoformat()}',border=True,align='C')
            pdf.cell(49,6,txt=f'No. De Folio: {str(folio)}',border=True,align='C',ln=True)
            # Linea Muerta
            pdf.cell(0,2,fill=True,ln=True)
            # Nombres De las Columnas
            pdf.cell(16,6,txt='UNI.',border=True,align='C')
            pdf.cell(122,6,txt='PRODUCTO',border=True,align='L')
            pdf.cell(29,6,text='PRECIO U.',border=True,align='R')
            pdf.cell(29,6,txt='TOTAL',border=True,align='R', ln=True)
            # Linea Muerta
            pdf.cell(0,2,fill=True,ln=True)
            # Iteramos en la tabla con datos de venta:
            for i,row in df_salida.iterrows():
                pdf.cell(16,6,txt=f'{row['Piezas']}',border=True,align='C') 
                pdf.cell(122,6,txt=f'{row['Producto']}',border=True,align='L') 
                pdf.cell(29,6,txt=f'$ {row['Precio']}',border=True,align='R') 
                pdf.cell(29,6,txt=f'$ {row['Total']}', ln=True,border=True,align='R')
            # Tamanho de la pagina pdf:
            half_page = (pdf.w / 2) - 10
            pdf.cell(0,2,fill=True,ln=True)
            pdf.cell(half_page,6,txt=f'Total De Productos: {productos_vendidos}', border=True, align='C')
            pdf.cell(half_page,6,txt=f'Total De Venta: $ {costos_totales}', border=True,align='C',ln=True)

            pdf_output = bytes(pdf.output(dest='S'))

            st.download_button(
                    label="Descargar PDF",
                    type='primary',
                    data=pdf_output,
                    key='descarga_venta_recibo',
                    file_name="Ticket Venta.pdf",
                    mime="application/pdf",
                    width='stretch'
                )

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


# LLAMADO A LAS FUNCIONES -----------------------------------------------------------------------------------------------------------

historial = acceso_a_historial()
folio = get_folio(historial)
productos = acceso_a_productos()
formulario_venta(folio=folio,data=productos)
