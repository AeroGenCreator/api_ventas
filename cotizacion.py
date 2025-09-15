import json

import lenguaje

from fpdf import FPDF
import streamlit as st
import pandas as pd

def cotizacion_funcion():
    """Esta Funcion Accede y Permite editar una tabla la cual calcula costos segun
    los productos listados en una cotizacion"""
    RUTA_PRODUCTOS = '_inventario_providencia.json'
        
    try:
        # Leo los datos de Productos, redondeo el precio de venta, creo la columna Producto Y Modelo
        # la asigno como el indice del DataFrame
        with open(RUTA_PRODUCTOS, 'r', encoding='utf-8') as file:
            df = pd.DataFrame(data=json.load(file))
            df['Precio Lista'] = round(df['Precio Lista'])
            
            # Las opciones de busqueda seran Producto Y Modelo
            OPCIONES = df['Producto'].to_list()
            
            #Creo un DataFrame vacio
            DF_VACIO = pd.DataFrame(
                {
                'Unidades':[None],
                'Producto':[None],
                'Precio U.':[None],
                'Total':[None],
                'Existencias':[None]
                }
            )

            # Inicializo contadores de items y costo total
            cotizacion_total = 0
            productos_en_cotizacion = 0

            # Asigno el DataFrame vacio y lo contadores al cache de streamlit
            if 'df_c' not in st.session_state:
                st.session_state.df_c = DF_VACIO
            if 'total'not in st.session_state:
                st.session_state.total = cotizacion_total
            if 'productos' not in st.session_state:
                st.session_state.productos = productos_en_cotizacion
            
            # Creo un DataFrame editable con filas dinamicas, asigno la salida a "edicion"
            edicion = st.data_editor(
                data=st.session_state.df_c,
                key='editor_cotizacion',
                num_rows='dynamic',
                column_order=['Unidades', 'Producto','Precio U.' ,'Total','Existencias'],
                hide_index=True,
                column_config={
                    'Unidades':st.column_config.NumberColumn(disabled=False,width=75,help=':orange[Unidades]',step=1),
                    'Producto':st.column_config.SelectboxColumn(options=OPCIONES,width=350,help=':orange[Producto Y Modelo]'),
                    'Precio U.':st.column_config.NumberColumn(format='dollar', disabled=True, width=50, help=':orange[Precio Unitario]'),
                    'Total':st.column_config.NumberColumn(disabled=True,width=50, format='dollar',help=':orange[Total]'),
                    'Existencias':st.column_config.TextColumn(disabled=True, width=60,help=':orange[Existencias]')
                }
            )
            
            # Inicializo los widgets para los contadores en la UI
            metric1,metric2 = st.columns([2,2])
            metric1.metric('Productos en la Cotizacion',value=st.session_state.productos,border=True)
            metric2.metric('Precio Total Cotizacion',value=st.session_state.total,border=True)

            # La salida "edicion" la convierto a DataFrame
            edicion = pd.DataFrame(edicion)

            # Creo los botones calculo, limpiar tabla, e imprimir
            col1, col2, col3 = st.columns(3)
            with col1:
                calcular_total = st.button('Calcular Total',width='stretch')
            with col2:
                limpiar_tabla = st.button('Limpiar - Cargar Cache',width='stretch')
            with col3:
                imprimir = st.button('Imprimir', type='primary', width='stretch')

            # Limpio el cache de streamlit para la situacion de limpiar una tabla.
            if edicion.empty:
                try:
                    st.session_state.df_c = DF_VACIO
                    st.session_state.total = cotizacion_total
                    st.session_state.productos = productos_en_cotizacion
                except(KeyError):
                    if 'df_c' not in st.session_state:
                        st.session_state.df_c = DF_VACIO
                    if 'total' not in st.session_state:
                        st.session_state.total = cotizacion_total
                    if 'productos' not in st.session_state:
                        st.session_state.productos = productos_en_cotizacion

            # Limpio la tabla y los contadores, asi mismo re-asigno DataFrame vacio y contadores vacios
            # Para el caso de tener eliminados los caches en streamlit.
            if limpiar_tabla:
                try:
                    st.session_state.df_c = DF_VACIO
                    st.session_state.total = cotizacion_total
                    st.session_state.productos = productos_en_cotizacion
                except(KeyError):
                    if 'df_c' not in st.session_state:
                        st.session_state.df_c = DF_VACIO
                    if 'total' not in st.session_state:
                        st.session_state.total = cotizacion_total
                    if 'productos' not in st.session_state:
                        st.session_state.productos = productos_en_cotizacion

            # Elimino filas vacias para Productos y Cantidades, elimino los duplicados de la tabla
            # manteniendo primeras apariciones. Si la tabla esta vacia, la reinicio en el cache.
            # Uno la salida "edicion" con "df" con sus indices correspondientes "Producto"
            if calcular_total or imprimir:
                edicion = edicion.dropna(axis=0,how='any',subset=['Unidades','Producto'])
                edicion = edicion.drop_duplicates(subset='Producto')
                if edicion.empty:
                    st.session_state.df_c = DF_VACIO
                else:
                    edicion['Producto'] = edicion['Producto'].apply(lambda x: x.strip().upper())
                    filtro = edicion['Producto'].tolist()
                    df = df[df['Producto'].isin(filtro)]
                    union = pd.merge(
                        df,
                        edicion,
                        how='left',
                        on='Producto'
                        )
                    # Hago el calculo de totales de la tabla y asigno totales a los contadores.
                    union['Precio Lista'] = round(union['Precio Lista'])
                    union['Precio U.'] = union['Precio Lista']
                    union['Total'] = union['Unidades'] * union['Precio Lista']
                    union['Existencias'] = union['Cantidad']

                    union = union.reindex(columns=['Unidades','Producto','Precio U.','Total','Existencias'])

                    cotizacion_total += union['Total'].sum()
                    productos_en_cotizacion += union['Unidades'].sum()

                    # Por ultimo se asignas al cache los nuevos datos para ser mostrados en la pantalla.
                    st.session_state.productos = productos_en_cotizacion
                    st.session_state.total = cotizacion_total
                    st.session_state.df_c = union
            
            if imprimir:
                # Creo una clase PDF con FPDF, la clase contendra header() y footer(), configuro alineacion, y colores
                class PDF(FPDF):
                    def __init__(self, orientation = "portrait", unit = "mm", format = "letter"):
                        super().__init__(orientation, unit, format)
                        self.add_font(family='ArialUnicodeMS',fname='arial-unicode-ms.ttf',uni=True)
                    def header(self):
                        self.set_text_color(0,0,0)
                        self.set_font(family='ArialUnicodeMS',size=20)
                        self.image('pro.jpg', 10, 8, 16)
                        self.cell(20,6,txt='Cotizacion', border=False,center=True,ln=True,align='C')
                        self.ln(15)
                    def footer(self):
                        self.set_y(-10)
                        self.set_font(family='ArialUnicodeMS',size=7)
                        self.cell(0,6,txt=f'Pagina {self.page_no()}/{{nb}}', center=True)
                    
                # Creo el resto de la hoja con PDF
                pdf = PDF(orientation='portrait',unit='mm',format='Letter')
                # Inicializo el auto salto de pagina
                pdf.set_auto_page_break(auto=True, margin=10)

                # Establezco los parametros de la hoja, fuente, color, tamanho
                pdf.add_page()
                pdf.set_font(family='ArialUnicodeMS',size=9)
                pdf.set_line_width(0.1)
                pdf.set_draw_color(224,224,224)
                pdf.set_fill_color(224,224,224)#204,255,229
                pdf.set_text_color(96,96,96)

                # Creo los nombre de las columnas, las cuales iran por encima de los datos de tabla
                pdf.cell(16,6,txt='UNI.',border=True,align='C') 
                pdf.cell(122,6,txt='PRODUCTO',border=True,align='C') 
                pdf.cell(29,6,txt='PRECIO U.',border=True,align='R') 
                pdf.cell(29,6,txt='TOTAL', ln=True,border=True,align='R')
                
                # Creo una linea muerta como separador
                pdf.cell(0,2,fill=True,ln=True)

                # Itero sobre los datos que estan en la tabla final guardada en el cache de streamlit
                # y los asigno a su celda pdf.
                for index, row in st.session_state.df_c.iterrows():
                    pdf.cell(16,6,txt=f'{row['Unidades']}',border=True,align='C') 
                    pdf.cell(122,6,txt=f'{row['Producto']}',border=True) 
                    pdf.cell(29,6,txt=f'$ {row['Precio U.']}',border=True,align='R') 
                    pdf.cell(29,6,txt=f'$ {row['Total']}', ln=True,border=True,align='R')

                # Dedermino el tamanho de mi pagina, lo divido y le resto 10 unidades.
                half_page = (pdf.w / 2) - 10

                # Determino formatos e imprimo los contadores al final de la tabla.
                pdf.cell(0,2,fill=True,ln=True)
                pdf.cell(half_page,6,txt=f'Total De Productos: {st.session_state.productos}', border=True, align='C')
                pdf.cell(half_page,6,txt=f'Total De Cotizacion: $ {st.session_state.total}', border=True,align='C',ln=True)
                
                # Guarda el PDF en un archivo temporal cpmo bytes, el output debe ser dest='S'
                pdf_output = bytes(pdf.output(dest='S'))
                
                # Proporciona el botón de descarga de streamlit y le asigno el pdf temporal.
                st.download_button(
                    label="Descargar PDF",
                    type='primary',
                    data=pdf_output,
                    file_name="cotizacion.pdf",
                    mime="application/pdf",
                    width=800
                )
    # Si hay problemas con la lectura se advierte la probable falta de datos.
    except (FileNotFoundError, json.JSONDecodeError, TypeError):
        st.warning('No Hay Productos En El :orange[Inventario]')

# Accededo al modulo de idioma, con la configuracion elegida por el usuario
l=lenguaje.tu_idioma()
# Titulo y llamo a la funcion de cotizacion:
st.header(f':material/request_quote: {l.phrase[3]}')
cotizacion_funcion()