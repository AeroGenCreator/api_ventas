"""Todas las funciones de el Menu Inventario se
manejan en este archivo"""
#Modulos Python
import os
import json
import re
import io
import zipfile

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

def lectura_del_inventario():
    try:
        if os.path.exists(PATH_PRODUCTOS) and os.path.getsize(PATH_PRODUCTOS)>0:
            with open(PATH_PRODUCTOS,'r',encoding='utf-8') as f:
                DataFrame = pd.DataFrame(json.load(f))
                return DataFrame
        else:
            return st.warning('No hay productos en el :orange[Inventario]')
    except (FileExistsError, json.JSONDecodeError):
        return st.error('Erro al acceder al :orange[Inventario] o al decodificarlo.')

def entrada_al_catalogo(entrada:dict):
    """Esta funcion agregar entradas nuevas de inventario 
    en la base de datos catalogo de productos"""
    try:
        # Aqui se evalua la existencia de la ruta y si existe informacion
        if os.path.exists(PATH_PRODUCTOS) and os.path.getsize(PATH_PRODUCTOS)>0:
            with open(PATH_PRODUCTOS, 'r', encoding='utf-8') as f:               
                
                # Parseo los datos de json a python.
                data = json.load(f)
                
                # Creo un DataFrame con los datos de lectura y otro con los datos nuevos
                df = pd.DataFrame(data)
                df_entrada = pd.DataFrame(entrada)

                # Este fragmento genera nuevos codigos para los nuevos datos asegurandose que no haya repetidos.
                codigos_existentes = set(df['Codigo'])
                nuevos_codigos = []
                while len(nuevos_codigos) < len(df_entrada):
                    nuevo_codigo = np.random.randint(10000000, 100000000)
                    if nuevo_codigo not in codigos_existentes:
                        nuevos_codigos.append(nuevo_codigo)
                df_entrada['Codigo'] = nuevos_codigos

                # Concateno los dos DataFrames:
                frames = [df, df_entrada]
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
        
                # Abro la ruta de la memoria ROM en modo escritura en f1 y guardo la nueva informacion
                with open(PATH_PRODUCTOS, 'w', encoding='utf-8') as f1:
                    json.dump(escritura_sin_duplicados, f1, indent=4, ensure_ascii=False)
                    
                    # Elimino la columna de mascara para el DataFrame con copias, si tiene datos lo muestro en pantalla:
                    df_incorrecto = df_incorrecto.drop(['Mascara'], axis=1)
                    if not df_incorrecto.empty:
                        st.warning('Los Siguientes Son Duplicados')
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
                    return st.success('DATOS AGREGADOS CON EXITO')
                
        else:
            # Si el archivo existe pero esta vacio, agrego directamente los nuevos datos:
            with open(PATH_PRODUCTOS,'w',encoding='utf-8') as f2:
                json.dump(entrada,f2,indent=4,ensure_ascii=False)
                return st.success('DATOS AGREGADOS CON EXITO')

    # En dado caso de tener problemas encontrando el archivo o con la decodificacion:     
    except(FileExistsError,FileNotFoundError,json.JSONDecodeError):
        with open(PATH_PRODUCTOS, 'w', encoding='utf-8') as f3:
            json.dump(entrada, f3, indent=4, ensure_ascii=False)
            return st.success('DATOS AGREGADOS CON EXITO')

def formulario_entrada_catalogo():
    """ En esta seccion se despliega un DataFrame editable. El usuario puede registrar productos
    en la base de datos """
    st.subheader('FORMULARIO DE ENTRADAS NUEVAS')
    
    # Creo un DataFrame Vacio y lo asigno la memomoria cache de streamlit
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
        }
    )
    if 'df_form' not in st.session_state:
        st.session_state.df_form = DF_FORMULARIO

    # Aqui declaro las opciones permitidas en la seleccion de unidades y unidades de medida
    opciones_seleccion_unidad = [
        'Pz (s)',
        'Bolsa (s)',
        'Caja (s)',
        'Ml-Gr (s)'
        ]
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
    'Excepto Para :green[Clave SAT, Precio Venta y Codigo]. El resto de :red[Campos] son obligatorios,' \
    'de lo contrario dicha fila no se guarda.\n ' \
    'Si un producto no cuenta con clave SAT el valor :green[None] es permitido :material/lightbulb:')

    # Aqui declaro el DataFrame editable y ajusto sus parametros para cada columna.
    salida = st.data_editor(
        st.session_state.df_form,
        num_rows='dynamic',
        hide_index=True,
        key='df_editable',
        column_config={
            'Clave SAT':st.column_config.TextColumn(
                width=66,
                help=':orange[Clave SAT]',
                pinned=True
            ),
            'Producto':st.column_config.TextColumn(
                width=200,
                help=':orange[Producto] (Maximo 40 Caracteres)',
                required=True,
                pinned=True,
                max_chars=40
            ),
            'Cantidad':st.column_config.NumberColumn(
                width=87,
                help=':orange[Cantidad]',
                required=True,
                min_value=0,
                step=1,
                pinned=True
            ),
            'Unidad':st.column_config.SelectboxColumn(
                width=77,
                help=':orange[Unidad]',
                required=True,
                options=opciones_seleccion_unidad,
                pinned=True
            ),
            'Dimension':st.column_config.TextColumn(
                width=95,
                help=':orange[Dimension] (Si el producto no tiene dimension ' \
                ':orange[agregar Sin Dimension])',
                validate='[0-9]|Sin Dimension',
                required=True,
                pinned=True
            ),
            'U. Medida':st.column_config.SelectboxColumn(
                width=93,
                help=':orange[U. Medida] ' \
                '(Si el producto no tiene U. Medida :orange[agregar "Sin Medida"])',
                required=True,
                options=opciones_seleccion_unidad_medida,
                pinned=True
            ),
            'Precio Compra':st.column_config.NumberColumn(
                width=99,
                help=':orange[Precio Compra]',
                required=True,
                min_value=0.00,
                step=0.01,
                format='dollar',
                pinned=True
            ),
            'Porcentaje Ganancia':st.column_config.NumberColumn(
                width=96,
                help=':orange[Porcentaje Ganancia]',
                required=True,
                min_value=0.01,
                max_value=1,
                step=0.01,
                format='percent',
                pinned=True
            ),
            'Precio Venta':st.column_config.NumberColumn(
                width=82,
                help=':orange[Precio Venta]',
                format='dollar',
                required=True,
                disabled=True,
                pinned=True
            ),
            'Codigo':st.column_config.NumberColumn(
                width=70,
                help=':orange[Codigo De Barras]',
                disabled=True,
                pinned=True
            )
        }
        )
    
    # DataFrame editable regresa un diccionario, lo convierto a pandas.DataFrame
    df = pd.DataFrame(salida)

    # Creo botones para la interfaz de usuario: calcular venta total, limpiar tabla, agregar productos:
    column1, column2 = st.columns(2)
    with column1:
        calcular = st.button(
        label=':material/calculate: __CALCULAR VENTA__',
        key='calculo',
        type='secondary',
        width=400,
        help=':orange[Calcula La columna Precio Venta Con Base En El Porcentaje Dado]'
        )   
    with column2:
        reset = st.button(
        label=':material/cleaning_services: __LIMPIAR TABLA__',
        type='secondary',
        width=400,
        key='reset_cache',
        help=':orange[Limpiar La Tabla Elimina Cualquier Registro]'
        )  
    agregar_data = st.button(
        label=':material/docs_add_on: __Agregar Productos__',
        key='agregar_data',
        type='primary', 
        width=800
        )
    
    if calcular:
                df['Precio Venta'] = df['Precio Compra'] * (1 + df['Porcentaje Ganancia'])
                st.session_state.df_form = df
    if reset:
                try:
                    st.session_state.df_form = DF_FORMULARIO
                except KeyError:
                    if 'df_form' not in st.session_state:
                        st.session_state.df_form = DF_FORMULARIO
    if agregar_data:
        # Convierto el DataFrame editable en pandas.DataFrame
        df = pd.DataFrame(salida)
        
        # Aqui reinicio el DataFrame guardado en el diccionario cache de Streamlit
        try:
            st.session_state.df_form = DF_FORMULARIO
        except KeyError:
            if 'df_form' not in st.session_state:
                st.session_state.df_form = DF_FORMULARIO
        
        # Aqui elimino las filas que no contengan datos en las columnas listadas (exepto para Clave SAT, P. Venta y Codigo)
        df = df.dropna(
            axis=0,
            how='any',
            subset=[
                'Producto',
                'Cantidad',
                'Unidad',
                'Dimension',
                'U. Medida',
                'Precio Compra',
                'Porcentaje Ganancia'
                ]
        )
        
        # Aqui evaluo si al eliminar filas tengo un DataFrame vacio. Y freno el proceso.
        if df.empty:
            st.warning('Ingrese :red[Valores] en la :red[Tabla]')
            return
        
        # Aqui calculo el precio de venta por si el usuario no lo hizo previamente
        df['Precio Venta'] = df['Precio Compra'] * (1 + df['Porcentaje Ganancia'])

        # Genero Codigos y limpio hasta estar seguro que no hay codigos duplicados
        codigos_generados = set()
        nuevos_codigos = []
        while len(nuevos_codigos) < len(df):
            nuevo_codigo = np.random.randint(10000000, 100000000)
            if nuevo_codigo not in codigos_generados:
                codigos_generados.add(nuevo_codigo)
                nuevos_codigos.append(nuevo_codigo)
        df['Codigo'] = nuevos_codigos

        # Aqui ocupo la libreria de numpy para tranformar los datos NaN a None para despues ser pasados a Null
        df = df.replace({np.nan: None})
        # Formateamos los numero en la columna Dimension dado que esta contiene strings y no numeros.
        patron1 = r'\.\d+'
        patron2 = r'0+\.\d+'
        df['Dimension'] = df['Dimension'].apply(lambda x: '0'+x if re.fullmatch(patron1,x) else str(float(x)) if re.fullmatch(patron2,x) else x)
        # Aqui aplico un formato de Mayusculas a la columna producto.
        df['Producto'] = df['Producto'].apply(lambda x: x.upper().strip())
        # Creo una columna que contiene Producto Y Modelo
        df['Entrada'] = df['Producto']+' '+df['Dimension']+' '+df['U. Medida']
        # Elimino los duplicados para la columna Producto Y Modelo
        df = df.drop_duplicates(subset=['Entrada'])
        # Elimino la columna Producto Y Modelo
        df = df.drop(columns=['Entrada'],axis=1)
        
        # Creo un diccionario con toda la informacion, las llaves son los nombre de columna y los datos son listas (tolist())
        dict_cache = df.to_dict(orient='list')
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
                        'Precio Compra': st.column_config.NumberColumn(format='dollar', width=100),
                        'Porcentaje Ganancia': st.column_config.NumberColumn(format='percent', width=135),
                        'Precio Venta': st.column_config.NumberColumn(format='dollar', width=100),
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

def ajustar_por_codigo():
    
    df = lectura_del_inventario()
    
    try:
        
        df.set_index('Codigo',inplace=True)
        
        copy = df.copy()
        copy['Producto Y Modelo'] = df['Producto']+' '+df['Dimension']+' '+df['U. Medida']
        copy['Cantidad'] = 0

        OPCIONES = df.index.tolist()
        
        escaner = st.multiselect(
            label='Escanea Los Codigos Deseados',
            options=OPCIONES
        )
        
        if escaner:
            salida = st.data_editor(
                data=copy[copy.index.isin(escaner)],
                column_order=['Producto Y Modelo','Cantidad'],
                column_config={
                    '_index':st.column_config.NumberColumn(disabled=True),
                    'Producto Y Modelo':st.column_config.TextColumn(disabled=True)
                }
            )

            guardar = st.button(
                label='Guardar Cambios',
                type='primary',
                key='guardar_cambios'
            )

            if guardar:
                salida.reset_index(inplace=True)
                df.loc[df.index.isin(salida['Codigo']),'Cantidad'] = salida['Cantidad'].values
                df.reset_index(inplace=True)
                df = df[[
                    'Clave SAT',
                    'Producto',
                    'Cantidad',
                    'Unidad',
                    'Dimension',
                    'U. Medida',
                    'Precio Compra',
                    'Porcentaje Ganancia',
                    'Precio Venta',
                    'Codigo'
                ]]
                datos = df.to_dict(orient='list')
                with open(PATH_PRODUCTOS,'w',encoding='utf-8')as e:
                    json.dump(datos,e,indent=4,ensure_ascii=False)
                st.success('Datos Ajustados Correctamente')
                st.stop()
    except st.errors.StreamlitAPIException:
        st.write('')

def crear_etiquetas_codigo():
    """" Es codigo genera codigos de barras y sus etiquetas para ser descargados"""
    try:
        # Leo los datos desde la base de datos y los cargo a un DataFrame
        if os.path.exists(PATH_PRODUCTOS) and os.path.getsize(PATH_PRODUCTOS) > 0:
            with open(PATH_PRODUCTOS,'r',encoding='utf-8') as f:
                df = pd.DataFrame(data=json.load(f))

            # Preparo las columnas que utilizare:
            df['Producto Y Modelo'] = df['Producto']+' '+df['Dimension']+' '+df['U. Medida']
            df['Codigo'] = df['Codigo'].astype('str')

            st.info('Si deseas todas las etiquetas no ingreses valores en la "Barra De Busqueda".')
            # Opcion de filtro y crear etiquetas para la interfaz de usuario:
            seleccion_especifica = st.multiselect(
                label='Selecciona Las Etiquetas Deseadas',
                key='seleccion_especifica',
                options=df['Producto Y Modelo'].tolist()
            )
            crear_etiquetas = st.button(
                label='Crear Etiquetas',
                key='crear_etiquetas',
                type='primary',
                width='stretch'
                )

            # Creacion de etiquetas
            if crear_etiquetas:
                
                # Aqui modifico las etiquetas que seran impresas si True, entonces filtro:
                if seleccion_especifica:
                    df = df[df['Producto Y Modelo'].isin(seleccion_especifica)]

                # Para el manejo de imagenes, establesco los parametros de 'fuente'
                try:
                    font_path_nombre = ImageFont.truetype('Ubuntu-B.ttf',16)
                except IOError:
                    font_path_nombre = ImageFont.load_default()
                
                # Crear un buffer de bytes para el archivo ZIP
                zip_buffer = io.BytesIO()
                with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                    # Itero sobre todos los productos 'DataFrame' o los productos 'seleccionados':
                    for index,row in df.iterrows():
                        
                        # Aqui genero el codigo de barras como imagen y edito sus parametros: 
                        code_128 = Code128(row['Codigo'], writer=ImageWriter())
                        barcode_img = code_128.render(writer_options={'module_height':9,'text_distance':3,'font_size':7})

                        # Aqui establezco el tamanho de las etiquetas finales:
                        LABEL_WIDTH=650
                        LABEL_HEIGHT=210

                        # Creo la imagen y su fondo, creo la clase de dibujo (edicion)
                        etiqueta_img = Image.new('RGB',(LABEL_WIDTH,LABEL_HEIGHT),'white')
                        draw = ImageDraw.Draw(etiqueta_img)

                        # Obtengo el tamanho de la imagen y calculo la posicicion para el codigo de barras.
                        barcode_width, barcode_height = barcode_img.size
                        barcode_x =  (LABEL_WIDTH - barcode_width) // 2
                        barcode_y = ((LABEL_HEIGHT - barcode_height) // 2) + 15

                        # Pego el codigo de barras en la imagen:
                        etiqueta_img.paste(barcode_img,(barcode_x,barcode_y))

                        # Obtengo el tamanho del Nombre del Producto, calculo su posicicion en la etiqeuta, dibujo el nombre:
                        box_size = draw.textbbox((0,0),row['Producto Y Modelo'],font=font_path_nombre)
                        p_x = box_size[2] - box_size[0]
                        p_y = box_size[3] - box_size[1]
                        x_producto = (LABEL_WIDTH - p_x) // 2
                        y_producto = ((LABEL_HEIGHT - p_y) // 2) - 80
                        draw.text((x_producto,y_producto ), row['Producto Y Modelo'], font=font_path_nombre, fill='black')

                        img_buffer=io.BytesIO()
                        etiqueta_img.save(img_buffer,format='PNG')
                        img_buffer.seek(0)

                        nombre_limpio = row['Producto Y Modelo'].replace('/','_').replace('(','').replace(')','')
                        file_name = f'etiquetas_{nombre_limpio}.png'
                        zip_file.writestr(file_name, img_buffer.getvalue())

                st.success('¡Etiquetas generadas! Haz clic en el botón para descargar.')

                zip_buffer.seek(0)

                st.download_button(
                    label='Descargar Etiquetas (ZIP)',
                    data=zip_buffer.getvalue(),
                    file_name='etiquetas_productos.zip',
                    mime='application/zip'
                )
                        

    # Aqui manejo inventario vacio o error de lectura:
        else:
            st.warning('No Hay Productos En El :orange[Inventario]')
    except(json.JSONDecodeError):
        st.error('Error Al Acceder Al Archivo De Inventario')


# ---------------------------------------------------------------------------------------------------------------------------------
# AQUI COMIENZA LA EJECUCION DEL ARCHIVO ------------------------------------------------------------------------------------------

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
    ajustar_por_codigo()

if seleccion_inventario_opciones == ':material/label: Imprimir Etiquetas de Codigo':
    crear_etiquetas_codigo()