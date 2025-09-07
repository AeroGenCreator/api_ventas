"""Todas las funciones de el Menu Inventario se
manejan en este archivo"""
#Modulos Python
import os
import json
import re

#Modulos Propios
import lenguaje

#Modulos de terceros
import streamlit_tags as tgs
import streamlit as st
import pandas as pd
import numpy as np
from barcode.codex import Code128
from barcode.writer import ImageWriter
from PIL import Image, ImageDraw, ImageFont

# Direccion json para el guardado de productos.
PATH_PRODUCTOS = 'catalogo_productos.json'

def entrada_al_catalogo(entrada:dict):
    """Esta funcion agregar entradas nuevas de inventario 
    en la base de datos catalogo de productos"""

        # Aqui se evalua la existencia de la ruta.
        # Primero evaluo si existe el archivo y si contiene informacion 
    try:
        with open(PATH_PRODUCTOS, 'r', encoding='utf-8') as l_file:               
            # Parseo los datos de json a python.
            data = json.load(l_file)
            # Creo un DataFrame con los datos de lectura
            df_data = pd.DataFrame(data)
            # Creo un DataFrame con los datos recibidos desde el "Formulario de Entradas"
            df_entrada = pd.DataFrame(entrada)

            codigos_existentes = df_data['Codigo'].to_list()
            codigos_repetidos = []
            df_entrada['Codigo'].apply(lambda x: codigos_repetidos.append(x) if x in codigos_existentes else x)
            df_entrada = df_entrada[~df_entrada['Codigo'].isin(codigos_repetidos)]
            df_codigos_duplicados = df_entrada[df_entrada['Codigo'].isin(codigos_repetidos)]

            if not df_codigos_duplicados.empty:
                st.warning('Se Repitieron Los Siguientes Codigos de Barras:')
                return st.dataframe(df_codigos_duplicados)
            else:
                if df_entrada.empty:
                    st.warning('Se Repitieron Los Siguientes Codigos de Barras:')
                    return st.dataframe(df_codigos_duplicados)
                else:
                    # Listo ambos DataFrames en 'frames'
                    frames = [df_data, df_entrada]
                    # Los concateno
                    df_unido = pd.concat(frames)
                    # Creo una mascara la cual busca duplicados para aquellos que cumplan con el Subset de columnas listadas:
                    df_unido['Mascara'] = df_unido.duplicated(subset=['Producto','Dimension','U. Medida'])

                    # Creo un DataFrame sin copias
                    df_correcto = df_unido[df_unido['Mascara'] == False]
                    # Creo un Dataframe con las copias
                    df_incorrecto = df_unido[df_unido['Mascara'] == True]

                    # Creo un diccionario con las nuevas entradas.
                    escritura_sin_duplicados = {
                        'Clave SAT':df_correcto['Clave SAT'].tolist(),
                        'Producto':df_correcto['Producto'].tolist(),
                        'Cantidad':df_correcto['Cantidad'].tolist(),
                        'Unidad':df_correcto['Unidad'].tolist(),
                        'Dimension':df_correcto['Dimension'].tolist(),
                        'U. Medida':df_correcto['U. Medida'].tolist(),
                        'Precio Compra':df_correcto['Precio Compra'].tolist(),
                        'Porcentaje Ganancia':df_correcto['Porcentaje Ganancia'].tolist(),
                        'Precio Venta':df_correcto['Precio Venta'].tolist(),
                        'Codigo':df_correcto['Codigo'].to_list()
                    }
        # Abro la ruta de la memoria ROM en modo escritura en e_file
        with open(PATH_PRODUCTOS, 'w', encoding='utf-8') as e_file:
            # Parseo y escribo el diccionario con las nuevas entras y sin repetidos
            json.dump(escritura_sin_duplicados, e_file, indent=4, ensure_ascii=False)
            # Elimino la columna de mascara para el DataFrame con copias
            df_incorrecto = df_incorrecto.drop(['Mascara'], axis=1)
            # Si el DataFrame NO esta vacio lo muestro en pantalla con el siguiente mensaje
            if not df_incorrecto.empty:
                duplicados_al_agregar = st.chat_message(name='human')
                with duplicados_al_agregar:
                    st.write(':orange[LOS SIGUIENTES SON DATOS DUPLICADOS]')
                    st.dataframe(
                        df_incorrecto,
                        column_config={
                            'Precio Compra':st.column_config.NumberColumn(format='dollar', width=50),
                            'Porcentaje Ganancia':st.column_config.NumberColumn(format='percent', width=50),
                            'Precio Venta':st.column_config.NumberColumn(format='dollar',width=50)
                        }
                        )
                    st.error('NO HAN SIDO SOBRE-ESCRITOS')
                    return
            # Si el DataFrame de duplicados si esta vacio, regresa el siguiente mensaje:    
            else:
                return st.success('DATOS AGREGADOS CON EXITO')
                
    except(FileNotFoundError, json.JSONDecodeError):
        # En dado caso que el archivo ROM no exista o este vacio, lo creamos con la ruta PATH_PRODUCTOS en modo escritura.
        with open(PATH_PRODUCTOS, 'w', encoding='utf-8') as ex_file:
            # Creamos un diccionario con los nombres de columnas correctos y sus valores obetenidos desde el parametro entrada
            # dado por el "Formula de Entradas"
            entrada_else = {
                'Clave SAT':entrada['Clave SAT'],
                'Producto':entrada['Producto'],
                'Cantidad':entrada['Cantidad'],
                'Unidad':entrada['Unidad'],
                'Dimension':entrada['Dimension'],
                'U. Medida':entrada['U. Medida'],
                'Precio Compra':entrada['Precio Compra'],
                'Porcentaje Ganancia':entrada['Porcentaje Ganancia'],
                'Precio Venta':entrada['Precio Venta'],
                'Codigo':entrada['Codigo']
            }
            # Parseamos y escribimos en el archivo json
            json.dump(entrada_else, ex_file, indent=4, ensure_ascii=False)
            # Mandamos el siguiente mensaje:
            return st.success('EDATOS AGREGADOS CON EXITO')

def formulario_entrada_catalogo():
    """En esta seccion se despliega un DataFrame editable. El usuario puede registrar productos
    en la base de datos.
    """

    st.subheader('FORMULARIO DE ENTRADAS NUEVAS')
    
    DF_FORMULARIO = pd.DataFrame(
        {
            'Clave SAT':[None],
            'Producto':[None],
            'Cantidad':[None],
            'Unidad':[None],
            'Dimension':[None],
            'U. Medida':[None],
            'Precio Compra':[None],
            'Porcentaje Ganancia':[None],
            'Precio Venta':[None],
            'Codigo':[None]
        },
        index=[0,1,2,3,4,5,6,7,8,9]
    )
    # st.session_state.df_vacio
    if 'df_formulario' not in st.session_state:
        st.session_state.df_formulario = DF_FORMULARIO

    # Aqui declaro las opciones permitidas en la seleccion de unidades para la columna 'Unidad' del DataFrame editable.
    opciones_seleccion_unidad = [
        'Pz (s)',
        'Bolsa (s)',
        'Paquete (s)',
        'Ml / Gr (s)'
        ]
    
    # Aqui declaro las opciones permitidas en la seleccion de unidades para la columna 'Unidades de Medida' del DataFrame editable.
    opciones_seleccion_unidad_medida = [
        'Kg (s)',
        'Lt (s)',
        'Mt (s)',
        'Mt (s) Cuadrado (s)',
        'Pulgada (s)',
        'Pz (s)',
        'Sin Medida'
        ]

    st.info(':material/lightbulb: Todas las columnas requieren un valor distinto de :red[None].\n' \
    'Todos los :red[Campos] son obligatorios, de lo contrario dicha fila no se guarda.\n ' \
    'Si un producto no cuenta con clave SAT el valor :green[None] es permitido :material/lightbulb:')

    # Aqui declaro el DataFrame editable y ajusto sus parametros para cada columna.
    # Ademas que el DataFrame editable que se muestra es el que cargue previamente en la memoria cache (st.session_state['df'])
    df_editable = st.data_editor(
        st.session_state.df_formulario,
        hide_index=True,
        key='df_editable',
        column_config={
            'Clave SAT':st.column_config.TextColumn(
                width=60,
                help=':orange[Clave SAT]',
                required=True,
                pinned=True
            ),
            'Producto':st.column_config.TextColumn(
                width=150,
                help=':orange[Producto] (Maximo 28 Caracteres)',
                required=True,
                pinned=True,
                max_chars=35
            ),
            'Cantidad':st.column_config.NumberColumn(
                width=40,
                help=':orange[Cantidad]',
                required=True,
                min_value=0,
                step=1,
            ),
            'Unidad':st.column_config.SelectboxColumn(
                width=60,
                help=':orange[Unidad]',
                required=True,
                options=opciones_seleccion_unidad
            ),
            'Dimension':st.column_config.TextColumn(
                width=50,
                help=':orange[Dimension] (Si el producto no tiene dimension ' \
                ':orange[agregar Sin Dimension])',
                validate='[0-9]'
            ),
            'U. Medida':st.column_config.SelectboxColumn(
                width=90,
                help=':orange[U. Medida] ' \
                '(Si el producto no tiene U. Medida :orange[agregar "Sin Medida"])',
                required=True,
                options=opciones_seleccion_unidad_medida
            ),
            'Precio Compra':st.column_config.NumberColumn(
                width=60,
                help=':orange[Precio Compra]',
                required=True,
                default=0.00,
                min_value=0.00,
                step=0.01,
                format='dollar'
            ),
            'Porcentaje Ganancia':st.column_config.NumberColumn(
                width=50,
                help=':orange[Porcentaje Ganancia]',
                required=True,
                default=0.01,
                min_value=0.01,
                max_value=1,
                step=0.01,
                format='percent'
            ),
            'Precio Venta':st.column_config.NumberColumn(
                width=60,
                help=':orange[Precio Venta]',
                format='dollar',
                required=True,
                disabled=True
            ),
            'Codigo':st.column_config.NumberColumn(
                width=60,
                help=':orange[Codigo De Barras]',
                disabled=True
            )
        }
        )
    
    column1, column2 = st.columns(2)

    # Este boton calcula la columna venta para el formulario que esta llenando el usuario
    with column1:
        calcular = st.button(
        label=':material/calculate: __CALCULAR VENTA__',
        key='calculo',
        type='secondary',
        width=400,
        help=':orange[Calcula La columna Precio Venta Con Base En El Porcentaje Dado]'
        )
        if calcular:
            df_editable['Precio Venta'] = df_editable['Precio Compra'] * (1 + df_editable['Porcentaje Ganancia'])
            st.session_state.df_formulario = df_editable
    # Este boton elimina el session_state.df_formulario, o sea lo limpia para comenzar de cero.
    with column2:
        reset = st.button(
        label=':material/cleaning_services: __LIMPIAR TABLA__',
        type='secondary',
        width=400,
        key='reset_cache',
        help=':orange[Limpiar La Tabla Elimina Cualquier Registro]'
        )
        if reset:
            del st.session_state.df_formulario

    # Aqui se valida la agreacion de producto a la memoria ROM ('catalogo_productos.json')
    agregar_data = st.button(
        label=':material/docs_add_on: __Agregar Productos__',
        key='agregar_data',
        type='primary', 
        width=800
        )
    
    if agregar_data:
        
        # Aqui reinicio el DataFrame guardado en el diccionario cache de Streamlit
        del st.session_state.df_formulario
        
        # Aqui calculo el precio de venta por si el usuario no lo hizo previamente
        df_editable['Precio Venta'] = df_editable['Precio Compra'] * (1 + df_editable['Porcentaje Ganancia'])
        df_editable['Codigo']=np.random.randint(10000000,100000000)
        # Aqui elimino las filas que no contengan datos en las columnas listadas (exepto para Clave SAT)
        # Los productos sin Clave SAT guardan su valor SAT como Null en Json
        df_editable = df_editable.dropna(
            axis=0,
            how='any',
            subset=[
                'Producto',
                'Cantidad',
                'Unidad',
                'Dimension',
                'U. Medida',
                'Precio Compra',
                'Porcentaje Ganancia',
                'Precio Venta',
                'Codigo'
                ]
        )

        # Aqui evaluo si al eliminar filas tengo un DataFrame vacio. Y freno el proceso.
        if df_editable.empty:
            st.warning('Ingrese :red[Valores] en la :red[Tabla]')
            return
        
        # Si hay datos despues del filtro anterior, continuo con el guardado.
        else:

            # Creo una copia del DataFrame
            df_a_guardar = df_editable.copy()
            # Aqui ocupo la libreria de numpy para tranformar los datos NaN a None para despues ser pasados a Null
            df_a_guardar = df_a_guardar.replace({np.nan: None})
            # Formateamos los numero en la columna Dimension dado que esta contiene strings y no numeros.
            patron1 = r'\.\d+'
            patron2 = r'0+\.\d+'
            df_a_guardar['Dimension'] = df_a_guardar['Dimension'].apply(lambda x: '0'+x if re.fullmatch(patron1,x) else str(float(x)) if re.fullmatch(patron2,x) else x)
            # Aqui aplico un formato de titulo a la columna producto.
            df_a_guardar['Producto'] = df_a_guardar['Producto'].apply(lambda x: x.upper().strip())
            # Creo una columna que contiene Producto Y Modelo
            df_a_guardar['Entrada'] = df_a_guardar['Producto']+' '+df_a_guardar['Dimension']+' '+df_a_guardar['U. Medida']
            # Elimino los duplicados para la columna Producto Y Modelo
            df_a_guardar = df_a_guardar.drop_duplicates(subset=['Entrada','Codigo'])
            # Elimino la columna Producto Y Modelo
            df_a_guardar = df_a_guardar.drop(columns=['Entrada'])
            
            # Creo un diccionario con toda la informacion, las llaves son los nombre de columna y los datos son listas (tolist())
            dict_cache = df_a_guardar.to_dict(orient='list')
            # Ocupo la funcion, que agrega a la memoria ROM 'catalogo_productos.json'
            entrada_al_catalogo(dict_cache)

            # Muestro un link para volver a inicio y finalizo la funcion.
            st.page_link(label=':material/arrow_back: Volver A Inicio', page='inicio.py', use_container_width=True)
            st.stop() 

def ver_inventario_completo():
    # Probamos la existencia y el tamabho del archivo en la ruta 'catalogo_productos.json'
    try:
        if os.path.exists(PATH_PRODUCTOS) and os.path.getsize(PATH_PRODUCTOS) > 0:
            # Si se pasa el primer filtro abrimos el archivo json en lectura
            with open(PATH_PRODUCTOS, 'r', encoding='utf-8') as lectura_file:
                
                datos = json.load(lectura_file)
                df = pd.DataFrame(datos)
                #Creamos una copia del DataFrame y creo una columna que une Producto, Dimension Y U. Medida
                df_copia = df.copy()
                df_copia['Producto Y Modelo'] = df_copia['Producto'] + ' ' + df_copia['Dimension'] + ' ' + df_copia['U. Medida']
                # Elimino las columnas Producto, Dimension Y U. Medida
                df_copia = df_copia.drop(['Producto','Dimension','U. Medida'], axis=1)
                # Re ordeno las columnas incluyendo la nueva
                columnas_orden = ['Clave SAT','Producto Y Modelo','Cantidad','Unidad','Precio Compra','Porcentaje Ganancia','Precio Venta','Codigo']
                df_copia = df_copia.reindex(columns=columnas_orden)
                # Coloco un filtro de Clave SAT y NO
                sat_filtro = st.toggle(
                    label='Filtrar Únicamente Productos con Clave SAT',
                    key='filtro_clave_sat'
                )
                # Para el filtro SAT, se eliminan todas las filas con valores NaN
                if sat_filtro:
                    df_filtrado = df_copia.dropna(subset=['Clave SAT'])
                    # Guardo los produtos que si tienen clave SAT
                    opciones_busqueda = df_filtrado['Producto Y Modelo']
                else:
                    df_filtrado = df_copia.copy()
                    # Hago una copia del DataFrame y guardo todos los productos en una lista, tanto los que tienen
                    # clave SAT como los que no.
                    opciones_busqueda = df_filtrado['Producto Y Modelo']
                
                # Este widget permite buscar productos basado en las opciones de busqueda establecidas
                # en sat_filtro.
                busqueda_seleccionada = st.multiselect(
                    'Buscar Producto',
                    key='busqueda_seleccionada',
                    options=opciones_busqueda
                )

                # Aplicar la búsqueda si se ha seleccionado algo
                if busqueda_seleccionada:
                    df_final = df_filtrado[df_filtrado['Producto Y Modelo'].isin(busqueda_seleccionada)]
                else:
                    df_final = df_filtrado
                
                # Visualización: Un solo lugar para mostrar el DataFrame
                return st.dataframe(
                    df_final.sort_values(by='Producto Y Modelo', ascending=True).reset_index(drop=True),
                    hide_index=True,
                    column_config={
                        'Producto Y Modelo':st.column_config.TextColumn(width=210),
                        'Precio Compra': st.column_config.NumberColumn(format='dollar', width=60),
                        'Porcentaje Ganancia': st.column_config.NumberColumn(format='percent', width=60),
                        'Precio Venta': st.column_config.NumberColumn(format='dollar', width=60),
                    }
                )
        # Si no hay registros en el inventario se muestra el sig. mensaje:        
        else:
            return st.info('No hay productos en el :orange["Inventario"]. ' \
            'Dirígete al sub-menú "Inventario/Agregar Producto"')
    except(FileNotFoundError, json.JSONDecodeError,TypeError):
        st.warning('No Hay Productos en el :orange[Inventario]')

def ajuste_cantidad_cpp():

    st.subheader('Ajuste - Costo Promedio Ponderado')
    try:
        
        with open(PATH_PRODUCTOS,'r',encoding='utf-8') as file:
            datos = json.load(file)
            # Creo un DataFrame con los datos originales y otro que sera editado
            df = pd.DataFrame(data=datos)
            df_copia = df.copy()
            # Creo la columna Producto Y Modelo en ambos DataFrame
            df['Producto Y Modelo'] = df['Producto']+' '+df['Dimension']+' '+df['U. Medida']
            df_copia['Producto Y Modelo'] = df_copia['Producto']+' '+df_copia['Dimension']+' '+df_copia['U. Medida']
            # Establesco los Indices como "Producto Y Modelo"
            df = df.set_index('Producto Y Modelo')
            df_copia = df_copia.set_index('Producto Y Modelo')
            # Para el DataFrame que se editara creo columnas que recibiran los ajustes:
            df_copia['Nueva Cantidad'] = 0
            df_copia['Nuevo Precio C.'] = 0.0
            st.info('Solo se pueden editar las columnas (:green[Nueva Cantidad], :green[Nuevo Precio C.])')
            # Creo el filtro de busqueda
            opciones_busqueda = df_copia.index
            busqueda = st.multiselect(
                label='Buscar Producto',
                options=opciones_busqueda
            )
            # Filtro el DataFrame que se mostrara
            df_copia = df_copia[df_copia.index.isin(busqueda)]
            df_copia = df_copia.reindex(columns=[
                'Cantidad',
                'Nueva Cantidad',
                'Precio Compra',
                'Nuevo Precio C.',
                'Porcentaje Ganancia',
                'Precio Venta'
                ])
            if busqueda:
                # Muestro el DataFrame que sera editado y lo asigno a la variable df_ajuste
                df_ajuste = st.data_editor(
                    df_copia,
                    hide_index=False,
                    column_config={
                        '_index':st.column_config.TextColumn(disabled=True),
                        'Cantidad':st.column_config.NumberColumn(disabled=True,width=50),
                        'Nueva Cantidad':st.column_config.NumberColumn(step='int',width=50),
                        'Precio Compra':st.column_config.NumberColumn(disabled=True,format='dollar',step='float',width=50),
                        'Nuevo Precio C.':st.column_config.NumberColumn(format='dollar',step=0.01,width=50),
                        'Porcentaje Ganancia':st.column_config.NumberColumn(disabled=True,format='percent',width=50),
                        'Precio Venta':st.column_config.NumberColumn(disabled=True,format='dollar',width=50)
                    }
                    )
                # Calculamos el Costo Promedio Ponderado
                ajustar = st.button(':green[__Realizar Ajuste__]')
                if ajustar:
                    df_ajuste['Costo Actual Inventario'] = df_ajuste['Cantidad'] * df_ajuste['Precio Compra']
                    df_ajuste['Costo Nuevo Inventario'] = df_ajuste['Nueva Cantidad'] * df_ajuste['Nuevo Precio C.']
                    df_ajuste['Costo Total Inventario'] = df_ajuste['Costo Actual Inventario'] + df_ajuste['Costo Nuevo Inventario']
                    df_ajuste['Unidades Totales Inventario'] = df_ajuste['Cantidad'] + df_ajuste['Nueva Cantidad']
                    df_ajuste['Costo Promedio Ponderado'] = round(df_ajuste['Costo Total Inventario'] / df_ajuste['Unidades Totales Inventario'],2)
                    
                    # Calculamos el nuevo Precio de Venta
                    df_ajuste['Nuevo Precio Venta'] = round(df_ajuste['Costo Promedio Ponderado'] * (1 + df_ajuste['Porcentaje Ganancia']),2)

                    # Escribimos los nuevos valores en el inventario real utilizando df original:
                    df.loc[df_ajuste.index,['Cantidad','Precio Compra','Precio Venta']] = df_ajuste[['Unidades Totales Inventario','Costo Promedio Ponderado','Nuevo Precio Venta']].values
                    df_muestra = df.copy()
                    df = df.reset_index().drop(columns=['Producto Y Modelo'])
                    nuevos_datos = df.to_dict(orient='list')
                    with open(PATH_PRODUCTOS,'w',encoding='utf-8') as file_guardar:
                        json.dump(nuevos_datos, file_guardar, indent=4, ensure_ascii=False)
                        st.dataframe(
                            df_muestra[df_muestra.index.isin(df_ajuste.index)],
                            column_order=['Cantidad','Precio Compra','Porcentaje Ganancia','Precio Venta'],
                            column_config={
                                'Precio Compra':st.column_config.NumberColumn(format='dollar',width=50),
                                'Porcentaje Ganancia':st.column_config.NumberColumn(format='percent',width=50),
                                'Precio Venta':st.column_config.NumberColumn(format='dollar',width=50)
                            }
                            )
                        st.success('Datos Guardados Correctamente Ajustando el Costo del Inventario')
                        st.stop()
    except (FileNotFoundError, json.JSONDecodeError, TypeError):
        st.warning('No Hay Productos en el :orange[Inventario]')

def ajustar_inventario():
    st.subheader('Edicion de Unidades')
    try:
        # Leo los datos:
        if os.path.exists(PATH_PRODUCTOS) and os.path.getsize(PATH_PRODUCTOS) > 0:
            
            with open(PATH_PRODUCTOS, 'r', encoding='utf-8') as file_edit:
                # Cargo los datos del inventario
                inventario_edit = json.load(file_edit)
                # Creo un DataFrame con los datos originales
                df = pd.DataFrame(inventario_edit)
                # Creo una nueva columna con Porducto y Modelo en el DataFrame original
                df['Producto Y Modelo'] = df['Producto'] + ' ' + df['Dimension'] + ' ' + df['U. Medida']
                opciones_productos = df['Producto Y Modelo'].unique()
                
                st.info('Solo se pueden editar las columnas (:green[Cantidad], :green[Porcentaje Ganancia])')
                filtro_ajuste = st.multiselect(
                    label='Buscar Producto',
                    options=opciones_productos,
                    key='filtro_ajuste'
                )
                
                if filtro_ajuste:
                    # Una vez filtrados los productos deseados, muestro un dataframe que ignora las columnas
                    # Producto, Dimension, U. Medida
                    df_ajuste = df[df['Producto Y Modelo'].isin(filtro_ajuste)].copy()
                    df_mostrar = df_ajuste[['Clave SAT','Producto Y Modelo','Cantidad','Porcentaje Ganancia','Precio Venta']]
                    df_mostrar['Cantidad']=0
                    #Creo el DataFrame editable con sus parametros de edicion
                    df_ajustado = st.data_editor(
                        df_mostrar,
                        hide_index=True,
                        column_config={
                            'Producto Y Modelo':st.column_config.TextColumn(disabled=True),
                            'Clave SAT':st.column_config.TextColumn(disabled=True,width=80),
                            'Cantidad':st.column_config.NumberColumn(width=40,min_value=0,default=0),
                            'Porcentaje Ganancia':st.column_config.NumberColumn(format='percent',width=60,max_value=1,min_value=0.01),
                            'Precio Venta':st.column_config.NumberColumn(disabled=True,format='dollar',width=60)
                        }
                        )

                    guardar_ajustes = st.button(key='guardar_ajustes', label=':green[Guardar Ajustes]')
                    
                    if guardar_ajustes:
                        # Creo DataFrame_final estableciendo la columna 'Producto Y Modelo' como el indice
                        # Lo mismo para df_datos_nuevos
                        df_final = df.set_index('Producto Y Modelo')
                        df_datos_nuevos = df_ajustado.set_index('Producto Y Modelo')
                        # De manera vectorial 'pandas' remplazo los valores viejos con los valores nuevos:
                        df_final.loc[df_datos_nuevos.index,['Cantidad','Porcentaje Ganancia']] = df_datos_nuevos[['Cantidad','Porcentaje Ganancia']].values
                        # Calculo el Precio de venta
                        df_final['Precio Venta'] = round(df_final['Precio Compra'] * (1 + df_final['Porcentaje Ganancia']),2)
                        # transformo el DataFrame_Final a diccionario de listas = {k:[v]}
                        dict_editado = df_final.reset_index().drop(columns=['Producto Y Modelo']).to_dict(orient='list')
                        # Guardo los datos:
                        with open(PATH_PRODUCTOS, 'w', encoding='utf-8') as edicion_f:
                            json.dump(dict_editado, edicion_f, indent=4, ensure_ascii=False)             
                            
                            exito_edicion = st.chat_message(name='human')
                            
                            with exito_edicion:
                                # Muestro los cambios realizados:
                                st.write(':orange[__AJUSTES REALIZADOS__]')
                                # Desde el DataFrame_final seleccionando unicamente las filas editadas con datos_nuevos.index
                                df_para_mostrar = df_final.loc[df_datos_nuevos.index].reset_index()
                                # Mostramos el DataFrame
                                st.dataframe(
                                    df_para_mostrar.reindex(columns=[
                                        'Clave SAT',
                                        'Producto Y Modelo',
                                        'Cantidad',
                                        'Precio Compra',
                                        'Porcentaje Ganancia',
                                        'Precio Venta'
                                        ]),
                                    hide_index=True,
                                    column_config={
                                        'Cantidad':st.column_config.NumberColumn(width=50),
                                        'Precio Compra':st.column_config.NumberColumn(format='dollar',width=60),
                                        'Porcentaje Ganancia':st.column_config.NumberColumn(format='percent',width=60),
                                        'Precio Venta':st.column_config.NumberColumn(format='dollar',width=60)
                                    }
                                    )
                                st.badge(color='green', label='Datos Guardados :material/check:')
                        # Mostramos link a 'Inicio' y detengo el programa
                        st.page_link(label=':material/arrow_back: Volver A Inicio', page='inicio.py', use_container_width=True)
                        st.stop()
        else:
            return st.warning('No hay productos en el inventario')
    except(FileNotFoundError,json.JSONDecodeError,TypeError):
        st.warning('No Hay Productos en el :orange[Inventario]')

def eliminar_entradas():
    st.subheader('Eliminacion de Entradas')
    try:
        if os.path.exists(PATH_PRODUCTOS) and  os.path.getsize(PATH_PRODUCTOS) > 0:
            # Leo los datos
            with open(PATH_PRODUCTOS, 'r', encoding='utf-8') as l_file:
                # Parseo y creo el DataFrame original
                datos = json.load(l_file)
                df = pd.DataFrame(datos)
                # Creo la columna Producto Y Modelo
                df['Producto Y Modelo'] = df['Producto']+' '+df['Dimension']+' '+df['U. Medida']
                # Creo el filtro de busqueda
                opciones_seleccion = df['Producto Y Modelo']
                seleccion_eliminar = st.multiselect(
                    key='seleccion_eliminar',
                    label='Buscar Producto',
                    options=opciones_seleccion
                )

                if seleccion_eliminar:
                    # Muestro las selecciones del usuario
                    df_muestra = df[['Producto Y Modelo','Cantidad','Unidad','Precio Compra','Porcentaje Ganancia','Precio Venta']]
                    st.dataframe(
                        df_muestra[df_muestra['Producto Y Modelo'].isin(seleccion_eliminar)],
                        hide_index=True,
                        column_config={
                            'Precio Compra':st.column_config.NumberColumn(format='dollar',width=60),
                            'Porcentaje Ganancia':st.column_config.NumberColumn(format='percent',width=50),
                            'Precio Venta':st.column_config.NumberColumn(format='dollar', width=60)
                        }
                        )
                    st.info(':material/lightbulb: Al dar click en :red[Eliminar] ' \
                    'los cambios no pueden deshacercerse :material/lightbulb:')

                    eliminar_seleccionados = st.button(
                        label=':red[:material/delete: Eliminar Seleccionados]',
                        key='eliminar_seleccionados'
                        )
                    
                    if eliminar_seleccionados:
                        # Basado en los indices seleccionados por el usuario elimino las filas en el df original
                        df_muestra = df_muestra[df_muestra['Producto Y Modelo'].isin(seleccion_eliminar)]
                        df = df.drop(index=df_muestra.index)
                        # Elimino la columna 'Producto Y Modelo' Y parseo de DataFrame a diccionario de listas:
                        df = df.drop(columns=['Producto Y Modelo'])
                        entradas_corregidas = df.to_dict(orient='list')
                        # Guardo los cambio: Parseo el diccionario a json
                        with open(PATH_PRODUCTOS, 'w', encoding='utf-8') as g_file:
                            json.dump(entradas_corregidas, g_file,indent=4, ensure_ascii=False)

                        st.success('Productos Eliminados Correcatamente')

                        st.page_link(
                            label=':material/arrow_back: Volver A Inicio',
                            page='inicio.py',
                            use_container_width=True
                            )
                        st.stop()       
        else:
            return st.warning('No hay datos en el :red[Inventario]')
    except(FileNotFoundError,json.JSONDecodeError,TypeError):
        st.warning('No Hay Productos en el :orange[Inventario]')

def crear_etiquetas_codigo():
    try:
        if os.path.exists(PATH_PRODUCTOS) and os.path.getsize(PATH_PRODUCTOS) > 0:
            with open(PATH_PRODUCTOS,'r',encoding='utf-8') as f:
                datos = json.load(f)
                
                df = pd.DataFrame(data=datos)

                df['Producto Y Modelo'] = df['Producto']+' '+df['Dimension']+' '+df['U. Medida']
                df['Codigo'] = df['Codigo'].astype('str')
                producto_codigo = df[['Producto Y Modelo','Codigo']]

                crear_etiquetas = st.button(label='Crear Etiquetas', key='crear_etiquetas', type='primary',width='stretch')
                if crear_etiquetas:
                    output_dir = 'codigos_productos'
                    os.makedirs(output_dir, exist_ok=True)

                    try:
                        font_path_nombre = ImageFont.truetype('arial.ttf',24)
                        font_path_codigo = ImageFont.truetype('arial.ttf',20)
                    except IOError:
                        font_path_nombre = ImageFont.load_default()
                        font_path_codigo = ImageFont.load_default()
                        print("Advertencia: No se encontró 'arial.ttf'. Usando fuente por defecto de Pillow.")
                    
                    for index,row in producto_codigo.iterrows():
                        code_128 = Code128(row['Codigo'], writer=ImageWriter())
                        barcode_img = code_128.render(writer_options={'module_height':10,'text_distance':1,'font_size':10})

                        LABEL_WIDTH=500
                        LABEL_HEIGHT=200

                        etiqueta_img = Image.new('RGB',(LABEL_WIDTH,LABEL_HEIGHT),'white')
                        draw = ImageDraw.Draw(etiqueta_img)

                        barcode_width, barcode_height = barcode_img.size

                        barcode_x =  (LABEL_WIDTH - barcode_width) // 2
                        barcode_y = (LABEL_HEIGHT - barcode_height) // 2 - 30

                        etiqueta_img.paste(barcode_img,(barcode_x,barcode_y))

                        draw.text((100,10 ), row['Producto Y Modelo'], font=font_path_nombre, fill='black')

                        draw.text((100,10 ), row['Codigo'], font=font_path_codigo, fill='black')

                        output_filename = os.path.join(output_dir, f"etiqueta_{row['Codigo']}.png")
                        etiqueta_img.save(output_filename)

        else:
            st.warning('No Hay Productos En El :orange[Inventario]')
    except(json.JSONDecodeError):
        st.error('Error Al Acceder Al Archivo De Inventario')

l = lenguaje.tu_idioma()
st.title(f':material/inventory_2: {l.phrase[2]}')

seleccion_inventario_opciones = st.pills(
    key='agregar_entrada_al_inventario',
    label='',
    options=[
        f':material/inventory_2: {l.phrase[2]}',
        ':material/docs_add_on: Agregar Nuevo',
        ':material/difference: Ajuste Costo Promedio Ponderado',
        ':material/table_edit: Ajuste Simple',
        ':material/delete: Eliminar Producto',
        ':material/barcode_scanner: Ajustar Producto Con Scaner',
        ':material/label: Imprimir Etiquetas de Codigo',
        ],
    selection_mode='single',
    default=f':material/inventory_2: {l.phrase[2]}',
    )

if seleccion_inventario_opciones == f':material/inventory_2: {l.phrase[2]}':
    ver_inventario_completo()    
    
if seleccion_inventario_opciones == ':material/docs_add_on: Agregar Nuevo':
    formulario_entrada_catalogo()

if seleccion_inventario_opciones == ':material/difference: Ajuste Costo Promedio Ponderado':
    ajuste_cantidad_cpp()

if seleccion_inventario_opciones == ':material/table_edit: Ajuste Simple':
    ajustar_inventario()

if seleccion_inventario_opciones == ':material/delete: Eliminar Producto':
    eliminar_entradas()

if seleccion_inventario_opciones == ':material/barcode_scanner: Ajustar Producto Con Scaner':
    st.write('En Construccion')

if seleccion_inventario_opciones == ':material/label: Imprimir Etiquetas de Codigo':
    crear_etiquetas_codigo()