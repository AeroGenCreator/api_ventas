import json

import lenguaje

from fpdf import FPDF
import streamlit as st
import pandas as pd

# Accededo al modulo de idioma, con la configuracion elegida por el usuario
l=lenguaje.tu_idioma()

st.title(f':material/request_quote: {l.phrase[3]}')

RUTA_PRODUCTOS = 'catalogo_productos.json'
    
try:
    # Leo los datos de Productos, redondeo el precio de venta, creo la columna Producto Y Modelo
    # la asigno como el indice del DataFrame
    with open(RUTA_PRODUCTOS, 'r', encoding='utf-8') as file:
        datos = json.load(file)
        df = pd.DataFrame(data=datos)
        df['Precio Venta'] = round(df['Precio Venta'])
        df['Precio Unitario'] = df['Precio Venta']
        df['Precio Unitario'] = df['Precio Unitario'].astype('str')
        df['Producto Y Modelo'] = df['Producto']+' '+df['Dimension']+' '+df['U. Medida']
        df = df.set_index('Producto Y Modelo',drop=True)
        
        # Las opciones de busqueda seran Producto Y Modelo
        OPCIONES = df.index.to_list()
        
        #Creo un DataFrame vacio
        DF_VACIO = pd.DataFrame(
            {
            'Unidades':[None],
            'Producto Y Modelo':[None],
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
            column_order=['Unidades', 'Producto Y Modelo','Precio U.' ,'Total','Existencias'],
            hide_index=True,
            column_config={
                'Unidades':st.column_config.NumberColumn(disabled=False,width=50,help=':orange[Unidades]',step=1),
                'Producto Y Modelo':st.column_config.SelectboxColumn(options=OPCIONES,width=400,help=':orange[Producto Y Modelo]'),
                'Precio U.':st.column_config.NumberColumn(format='dollar', disabled=True, width=50, help=':orange[Precio Unitario]'),
                'Total':st.column_config.NumberColumn(disabled=True,width=50, format='dollar',help=':orange[Total]'),
                'Existencias':st.column_config.TextColumn(disabled=True, width=60,help=':orange[Existencias]')
            }
        )
        
        # Inicializo los widgets para los contadores en la UI
        metric1,metric2 = st.columns([2,2])
        metric1.metric('Productos en la Cotizacion', value=st.session_state.productos,border=True)
        metric2.metric('Precio Total Cotizacion',value=st.session_state.total, border=True)

        # La salida "edicion" la convierto a DataFrame
        edicion = pd.DataFrame(edicion)

        # Creo los botones calculo, limpiar tabla, e imprimir
        col1, col2, col3 = st.columns(3)
        with col1:
            calcular_total = st.button('Calcular Total',width=200)
        with col2:
            limpiar_tabla = st.button('Limpiar - Cargar Cache',width=200)
        with col3:
            imprimir = st.button('Imprimir', type='secondary', width=200)

        # Limpio el cache de streamlit para la situacion de limpiar una tabla.
        if edicion.empty:
            del st.session_state.df_c
            del st.session_state.total
            del st.session_state.productos

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
        # Uno la salida "edicion" con "df" con sus indices correspondientes "Producto Y Modelo"
        if calcular_total:
            edicion = edicion.dropna(axis=0,how='any',subset='Producto Y Modelo')
            edicion = edicion.drop_duplicates(subset='Producto Y Modelo')
            if edicion.empty:
                st.session_state.df_c = DF_VACIO
            else:
                linker = df.loc[edicion['Producto Y Modelo']]
                
                union = pd.merge(
                    edicion,
                    linker,
                    how='left',
                    on='Producto Y Modelo'
                    )
                # Hago el calculo de totales de la tabla y asigno totales a los contadores.
                union['Precio Venta'] = round(union['Precio Venta'])
                union['Precio U.'] = union['Precio Venta']
                union['Total'] = union['Unidades'] * union['Precio Venta']
                union['Existencias'] = union['Cantidad']

                union = union.reindex(columns=['Unidades','Producto Y Modelo','Precio U.','Total','Existencias'])
                
                cotizacion_total += union['Total'].sum()
                productos_en_cotizacion += union['Unidades'].sum()
                # Por ultimo se asignas al cache los nuevos datos para ser mostrados en la pantalla.
                st.session_state.productos = productos_en_cotizacion
                st.session_state.total = cotizacion_total
                st.session_state.df_c = union
        
        if imprimir:
            # Al impirmir, repito el calculo anterior.
            # Para tener los datos actualizados al momento de pasar a la impresion.
            edicion = edicion.dropna(axis=0,how='any',subset='Producto Y Modelo')
            edicion = edicion.drop_duplicates(subset='Producto Y Modelo')
            if edicion.empty:
                st.session_state.df_c = DF_VACIO
            else:
                linker = df.loc[edicion['Producto Y Modelo']]
                
                union = pd.merge(
                    edicion,
                    linker,
                    how='left',
                    on='Producto Y Modelo'
                    )
                
                union['Precio Venta'] = round(union['Precio Venta'])
                union['Precio U.'] = union['Precio Venta']
                union['Total'] = union['Unidades'] * union['Precio Venta']
                union['Existencias'] = union['Cantidad']

                union = union.reindex(columns=['Unidades','Producto Y Modelo','Precio U.','Total','Existencias'])
                
                cotizacion_total += union['Total'].sum()
                productos_en_cotizacion += union['Unidades'].sum()

                st.session_state.productos = productos_en_cotizacion
                st.session_state.total = cotizacion_total
                st.session_state.df_c = union
            
            # Creo una clase PDF con FPDF, la clase contendra header() y footer(), configuro alineacion, y colores
            class PDF(FPDF):
                def header(self):
                    self.set_text_color(0,51,0)
                    self.image('providencia_logo.jpeg', 10, 8, 16)
                    self.set_font(family='helvetica', size=12, style='B')
                    self.cell(20,6,txt='Ferreteria La Providecia: Cotizacion', border=False,ln=True, center=True,align='R')
                    self.ln(15)
                def footer(self):
                    self.set_y(-10)
                    self.set_font('helvetica',style='I',size=9)
                    self.cell(0,6,txt=f'Pagina {self.page_no()}/{{nb}}', center=True)
                
            # Creo el resto de la hoja con PDF
            pdf = PDF(orientation='portrait',unit='mm',format='Letter')

            # Inicializo el auto salto de pagina
            pdf.set_auto_page_break(auto=True, margin=10)

            # Establezco los parametros de la hoja, fuente, color, tamanho
            pdf.add_page()
            pdf.set_font("Arial", size=8)
            pdf.set_line_width(0.1)
            pdf.set_draw_color(245,222,179)
            pdf.set_fill_color(245,222,179)#204,255,229
            pdf.set_text_color(0,51,0)

            # Creo los nombre de las columnas, las cuales iran por encima de los datos de tabla
            pdf.cell(16,6,txt='Uni.',border=True,align='C') 
            pdf.cell(122,6,txt='Producto Y Modelo',border=True,align='C') 
            pdf.cell(29,6,txt='Precio U.',border=True,align='R') 
            pdf.cell(29,6,txt='Total', ln=True,border=True,align='R')
            
            # Creo una linea muerta como separador
            pdf.cell(0,6,fill=True,ln=True)

            # Itero sobre los datos que estan en la tabla final guardada en el cache de streamlit
            # y los asigno a su celda pdf.
            for index, row in st.session_state.df_c.iterrows():
                pdf.cell(16,6,txt=f'{row['Unidades']}',border=True,align='C') 
                pdf.cell(122,6,txt=f'{row['Producto Y Modelo']}',border=True) 
                pdf.cell(29,6,txt=f'$ {row['Precio U.']}',border=True,align='R') 
                pdf.cell(29,6,txt=f'$ {row['Total']}', ln=True,border=True,align='R')

            # Dedermino el tamanho de mi pagina, lo divido y le resto 10 unidades.
            half_page = (pdf.w / 2) - 10

            # Determino formatos e imprimo los contadores al final de la tabla.
            pdf.cell(0,6,fill=True,ln=True)
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