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
RUTA = '_inventario_providencia.json'

def lectura_del_inventario():
    try:
        if os.path.exists(RUTA) and os.path.getsize(RUTA)>0:
            with open(RUTA,'r',encoding='utf-8') as f:
                DataFrame = pd.DataFrame(json.load(f))
                return DataFrame
        else:
            return st.warning('No hay productos en el :orange[Inventario]')
    except (FileExistsError, json.JSONDecodeError):
        return st.error('Erro al acceder al :orange[Inventario] o con la Decodificacion.')

def entrada_al_catalogo(entrada:dict):
    """Esta funcion agregar entradas nuevas de inventario 
    en la base de datos catalogo de productos"""
    try:
        df = lectura_del_inventario()
        df_entrada = pd.DataFrame(entrada)

        # Este fragmento genera nuevos codigos para los nuevos datos asegurandose que no haya repetidos.
        codigos_existentes = set(df['Codigo'])
        nuevos_codigos = []
        while len(nuevos_codigos) < len(df_entrada):
            nuevo_codigo = np.random.randint(1000, 10000)
            if nuevo_codigo not in codigos_existentes:
                nuevos_codigos.append(nuevo_codigo)
        df_entrada['Codigo'] = nuevos_codigos

        # Concateno los dos DataFrames:
        frames = [df, df_entrada]
        union = pd.concat(frames)
        union.reset_index(inplace=True,drop=True)
        # Creo una mascara la cual busca duplicados para aquellos que cumplan con el Subset de columnas listadas:
        union['Mascara'] = union.duplicated(subset=['Producto'])
        # Creo un DataFrame sin copias
        df_correcto = union[union['Mascara'] == False]
        # Creo un Dataframe con las copias
        df_incorrecto = union[union['Mascara'] == True]

        # Creo un diccionario con las nuevas entradas.
        df_correcto = df_correcto.drop(labels='Mascara',axis=1)
        df_correcto = df_correcto.to_dict()

        # Abro la ruta de la memoria ROM en modo escritura en f1 y guardo la nueva informacion
        with open(RUTA, 'w', encoding='utf-8') as f1:
            json.dump(df_correcto, f1, indent=4, ensure_ascii=False)
            
            # Elimino la columna de mascara para el DataFrame con copias, si tiene datos lo muestro en pantalla:
            df_incorrecto = df_incorrecto.drop(['Mascara'], axis=1)
            if not df_incorrecto.empty:
                st.warning('Los Siguientes Son Duplicados')
                st.dataframe(
                    df_incorrecto,
                    column_config={
                        'Precio Compra':st.column_config.NumberColumn(format='dollar', width=50),
                        'Porcentaje Ganancia':st.column_config.NumberColumn(format='percent', width=50),
                        'Precio Lista':st.column_config.NumberColumn(format='dollar',width=50)
                    }
                    )
                st.error('NO HAN SIDO SOBRE-ESCRITOS')
                return
            # Si el DataFrame de duplicados si esta vacio, regresa el siguiente mensaje:    
            return st.success('DATOS AGREGADOS CON EXITO')

    # En dado caso de tener problemas encontrando el archivo o con la decodificacion:     
    except(FileExistsError,FileNotFoundError,json.JSONDecodeError, TypeError):
        with open(RUTA, 'w', encoding='utf-8') as f3:
            json.dump(entrada, f3, indent=4, ensure_ascii=False)
            return st.success('DATOS AGREGADOS CON EXITO')

def formulario_entrada_catalogo():
    """ En esta seccion se despliega un DataFrame editable. El usuario puede registrar productos
    en la base de datos """
    st.subheader(':material/docs_add_on: Formulario Nuevas Entradas')
    OPCIONES_FORM = 'OPCIONES_FORM.json'
    # Creo un DataFrame Vacio y lo asigno la memomoria cache de streamlit
    DF_FORMULARIO = pd.DataFrame(
        {
            'Codigo':[None],
            'Producto':[None],
            'Cantidad':[None],
            'Categoría 1':[None],
            'Categoría 2':[None],
            'Unidad':[None],
            'Precio Compra':[None],
            'Porcentaje Ganancia':[None],
            'Precio Lista':[None],
            'Clave':[None],
            'Oficial':[True]
        }
    )
    if 'df_form' not in st.session_state:
        st.session_state.df_form = DF_FORMULARIO

    # Aqui declaro las opciones permitidas para las secciones [categoria_1, categoria_2 y Unidad]
    try:
        if os.path.exists(OPCIONES_FORM) and os.path.getsize(OPCIONES_FORM) > 0:
            with open(OPCIONES_FORM,'r',encoding='utf-8') as f:
                data = json.load(f)
    except (FileExistsError,FileNotFoundError,json.JSONDecodeError):
        data = 'SIN OPCION'

    if isinstance(data,dict):
        categoria_1_opciones = data['categoria_1']
        categoria_2_opciones = data['categoria_2']
        unidades_opciones = data['unidades']
    else:
        categoria_1_opciones = data
        categoria_2_opciones = data
        unidades_opciones = data

    # Aqui declaro el DataFrame editable y ajusto sus parametros para cada columna.
    salida = st.data_editor(
        st.session_state.df_form,
        num_rows='dynamic',
        hide_index=True,
        key='df_editable',
        column_config={
            'Codigo':st.column_config.NumberColumn(
                width=55,
                help=':orange[Codigo Unico]',
                pinned=True,
                disabled=True
            ),
            'Producto':st.column_config.TextColumn(
                width=200,
                help=':orange[Producto] (Maximo 60 Caracteres)',
                required=True,
                pinned=True,
                max_chars=60
            ),
            'Cantidad':st.column_config.NumberColumn(
                width=90,
                help=':orange[Cantidad]',
                required=True,
                min_value=0,
                step=1,
                pinned=True
            ),
            'Categoría 1':st.column_config.SelectboxColumn(
                width=105,
                help=':orange[Seleccione Categoria]',
                required=True,
                options=categoria_1_opciones,
                pinned=True
            ),
            'Categoría 2':st.column_config.SelectboxColumn(
                width=105,
                help=':orange[Seleccione Categoria]',
                required=True,
                options=categoria_2_opciones,
                pinned=True
            ),
            'Unidad':st.column_config.SelectboxColumn(
                width=80,
                help=':orange[Seleccione Unidad]',
                required=True,
                options=unidades_opciones,
                pinned=True
            ),
            'Precio Compra':st.column_config.NumberColumn(
                width=122,
                help=':orange[Precio Compra]',
                required=True,
                min_value=1,
                step=0.01,
                format='dollar',
                pinned=True
            ),
            'Porcentaje Ganancia':st.column_config.NumberColumn(
                width=135,
                help=':orange[Porcentaje Ganancia]',
                required=True,
                min_value=0.01,
                max_value=1,
                step=0.01,
                format='percent',
                disabled=True,
                pinned=True
            ),
            'Precio Lista':st.column_config.NumberColumn(
                width=105,
                help=':orange[Precio Venta]',
                format='dollar',
                required=True,
                disabled=False,
                pinned=True
            ),
            'Clave':st.column_config.TextColumn(
                width=70,
                help=':orange[Clave de Producto]',
                disabled=False,
                pinned=True,
                max_chars=30
            ),
            'Oficial':st.column_config.CheckboxColumn(
                width=80,
                help='El Producto Es Oficial',
                required=True,
                disabled=False,
                pinned=True,
                default=True
            )
        }
        )
    
    # DataFrame editable regresa un diccionario, lo convierto a pandas.DataFrame
    df = pd.DataFrame(salida)

    # Creo botones para la interfaz de usuario: calcular porcentaje de ganancia:
    column1, column2 = st.columns(2)
    with column1:
        calcular = st.button(
        label=':material/calculate: __CALCULAR %GANANCIA__',
        key='calculo',
        type='secondary',
        width='stretch',
        help=':orange[Calcula La columna Porcentaje de Ganancia]'
        )   
    with column2:
        reset = st.button(
        label=':material/cleaning_services: __LIMPIAR TABLA__',
        type='secondary',
        width='stretch',
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
                if len(df['Precio Compra']) and len(df['Precio Lista']) > 0:
                    df['Porcentaje Ganancia'] = (1 * (df['Precio Lista'] - df['Precio Compra'])) / df['Precio Compra']
                    st.session_state.df_form = df
                else:
                    st.warning('Ingresa Valores Para las Columnas "Precio Compra y Precio Lista"')
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
        
        # Aqui elimino las filas que no contengan datos en las columnas listadas (exepto para Codigo Y % Ganancia)
        df = df.dropna(
            axis=0,
            how='any',
            subset=[
            'Producto',
            'Cantidad',
            'Categoría 1',
            'Categoría 2',
            'Unidad',
            'Precio Compra',
            'Precio Lista',
            'Oficial'
            ]
        )
        
        # Aqui evaluo si al eliminar filas tengo un DataFrame vacio. Y freno el proceso.
        if df.empty:
            st.warning('Ingrese :red[Valores] en la :red[Tabla]')
            return
        df['Clave'] = df['Clave'].fillna('SIN CLAVE')
        # Aqui calculo el % gancia por el si el usuario no lo hizo previamente
        df['Porcentaje Ganancia'] = (1 * (df['Precio Lista'] - df['Precio Compra'])) / df['Precio Compra']

        # Genero Codigos y limpio hasta estar seguro que no hay codigos duplicados
        codigos_generados = set()
        nuevos_codigos = []
        while len(nuevos_codigos) < len(df):
            nuevo_codigo = np.random.randint(1000, 10000)
            if nuevo_codigo not in codigos_generados:
                codigos_generados.add(nuevo_codigo)
                nuevos_codigos.append(nuevo_codigo)
        df['Codigo'] = nuevos_codigos

        # Aqui ocupo la libreria de numpy para tranformar los datos NaN a None para despues ser pasados a Null
        df = df.replace({np.nan: None})
        # Aqui aplico un formato de Mayusculas a la columna producto.
        df['Producto'] = df['Producto'].apply(lambda x: x.upper().strip())
        # Creo una columna que contiene Producto Y Modelo
        df['Entrada'] = df['Producto']+' '+df['Categoría 1']+' '+df['Categoría 2']+' '+df['Unidad']
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
    st.subheader(':material/inventory_2: Productos')
    # Probamos la existencia y el tamanho del archivo en la ruta '_inventario_providencia.json'
    try:
        if os.path.exists(RUTA) and os.path.getsize(RUTA) > 0:
            # Si se pasa el primer filtro abrimos el archivo json en lectura
            with open(RUTA, 'r', encoding='utf-8') as lectura_file:
                datos = json.load(lectura_file)
                df = pd.DataFrame(datos)

                #Creamos una copia del DataFrame y creo una columna que une Producto, Dimension Y U. Medida
                df_copia = df.copy()
                # Re ordeno las columnas incluyendo la nueva
                columnas_orden = [
                    'Codigo',
                    'Cantidad',
                    'Producto',
                    'Categoría 1',
                    'Categoría 2',
                    'Unidad',
                    'Precio Compra',
                    'Porcentaje Ganancia',
                    'Precio Lista',
                    'Clave',
                    'Oficial'
                    ]
                df_copia = df_copia.reindex(columns=columnas_orden)
                
                # Agrego un filtro para buscar por nombres:
                opciones_busqueda = df_copia['Producto'].tolist()
                busqueda_seleccionada = st.multiselect(
                    'Buscar Producto',
                    key='busqueda_seleccionada',
                    options=opciones_busqueda
                )

                # Aplicar la búsqueda si se ha seleccionado algo
                if busqueda_seleccionada:
                    df_copia = df_copia[df_copia['Producto'].isin(busqueda_seleccionada)]
                
                # Visualización: Un solo lugar para mostrar el DataFrame
                return st.dataframe(
                    df_copia.sort_values(by='Producto', ascending=True).reset_index(drop=True),
                    hide_index=True,
                    column_config={
                        'Codigo':st.column_config.NumberColumn(width=60),
                        'Producto':st.column_config.TextColumn(width=200),
                        'Cantidad': st.column_config.NumberColumn(width=70),
                        'Categoría 1':st.column_config.TextColumn(width=80),
                        'Categoría 2':st.column_config.TextColumn(width=80),
                        'Unidad':st.column_config.TextColumn(width=60),
                        'Precio Compra':st.column_config.NumberColumn(width=110,format='dollar'),
                        'Porcentaje Ganancia': st.column_config.NumberColumn(width=130,format='percent'),
                        'Precio Lista': st.column_config.NumberColumn(width=90,format='dollar'),
                        'Clave':st.column_config.TextColumn(width=90),
                        'Oficial':st.column_config.CheckboxColumn(width=60)
                    }
                )
        # Si no hay registros en el inventario se muestra el sig. mensaje:        
        else:
            return st.info('No hay productos en el :orange["Inventario"]. ' \
            'Dirígete al sub-menú "Inventario/Agregar Producto"')
    except(FileNotFoundError, json.JSONDecodeError,TypeError):
        st.warning('No Hay Productos en el :orange[Inventario]')

def ajustar_inventario():
    
    st.subheader(':material/table_edit: Ajustes De Inventario')
    try:
        # Leo los datos:
        if os.path.exists(RUTA) and os.path.getsize(RUTA) > 0:            
            with open(RUTA, 'r', encoding='utf-8') as file_edit:
                df = pd.DataFrame(json.load(file_edit))
                copia = df.copy()
                
                opciones_productos = df['Producto'].tolist()
                filtro_ajuste = st.multiselect(
                    label='Buscar Producto',
                    options=opciones_productos,
                    key='filtro_ajuste'
                )
                
                if filtro_ajuste:
                    copia = copia[copia['Producto'].isin(filtro_ajuste)]
                    
                    #Creo el DataFrame editable con sus parametros de edicion
                    ajuste = st.data_editor(
                        copia,
                        key='frame_editable',
                        num_rows='fixed',
                        hide_index=True,
                        column_order=['Producto','Cantidad','Precio Compra','Precio Lista'],
                        column_config={
                            '_index':st.column_config.NumberColumn(disabled=True),
                            'Producto':st.column_config.TextColumn(disabled=True,width=252,pinned=True),
                            'Cantidad':st.column_config.NumberColumn(pinned=True,width=150),
                            'Precio Compra':st.column_config.NumberColumn(format='dollar',pinned=True, width=150,min_value=0.01),
                            'Precio Lista':st.column_config.NumberColumn(format='dollar',pinned=True, width=150)
                        }
                        )

                    guardar_ajustes = st.button(key='guardar_ajustes', label=':green[Guardar Ajustes]')
                    
                    if guardar_ajustes:
                        # Los indices ahora seran la columna Producto
                        df = df.set_index('Producto')
                        ajuste = ajuste.set_index('Producto')
                        # Calculo el Porcentaje de Ganancia para los nuevos datos:
                        ajuste['Porcentaje Ganancia'] = (1 * (ajuste['Precio Lista'] - ajuste['Precio Compra'])) / ajuste['Precio Compra']
                        # De manera vectorial 'pandas' remplazo los valores viejos con los valores nuevos:
                        df.loc[ajuste.index,['Cantidad','Precio Compra','Porcentaje Ganancia','Precio Lista']] = ajuste[['Cantidad','Precio Compra','Porcentaje Ganancia','Precio Lista']].values
                        # transformo el DataFrame_Final a diccionario:
                        df = df.reset_index()
                        df = df[[
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
                        data = df.to_dict(orient='list')
                        # Guardo los datos:
                        with open(RUTA, 'w', encoding='utf-8') as f:
                            json.dump(data, f, indent=4, ensure_ascii=False)
                            
                            # Muestro los cambios realizados:
                            st.success('AJUSTES REALIZADOS')
                            # Desde el DataFrame_final seleccionando unicamente las filas editadas con datos_nuevos.index
                            ajuste = ajuste.reset_index()
                            # Mostramos el DataFrame
                            st.dataframe(
                                ajuste.reindex(columns=[
                                    'Producto',
                                    'Cantidad',
                                    'Precio Compra',
                                    'Porcentaje Ganancia',
                                    'Precio Lista'
                                ]),
                                hide_index=True,
                                column_config={
                                    'Producto':st.column_config.TextColumn(width=200),
                                    'Cantidad':st.column_config.NumberColumn(width=60),
                                    'Precio Compra':st.column_config.NumberColumn(format='dollar',width=60),
                                    'Porcentaje Ganancia':st.column_config.NumberColumn(format='percent',width=60),
                                    'Precio Lista':st.column_config.NumberColumn(format='dollar',width=60)
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
    st.subheader(':material/delete: Eliminar')
    try:
        if os.path.exists(RUTA) and  os.path.getsize(RUTA) > 0:
            # Leo los datos
            with open(RUTA, 'r', encoding='utf-8') as f:
                # Parseo y creo el DataFrame original
                df = pd.DataFrame(json.load(f))
                copia = df.copy()
                # Opciones de Busqueda
                opciones_seleccion = df['Producto'].tolist()
                seleccion_eliminar = st.multiselect(
                    key='seleccion_eliminar',
                    label='Buscar Producto',
                    options=opciones_seleccion
                )

                if seleccion_eliminar:
                    # Muestro las selecciones del usuario
                    st.dataframe(
                        copia[copia['Producto'].isin(seleccion_eliminar)],
                        hide_index=True,
                        column_config={
                            'Precio Compra':st.column_config.NumberColumn(format='dollar',width=60),
                            'Porcentaje Ganancia':st.column_config.NumberColumn(format='percent',width=50),
                            'Precio Lista':st.column_config.NumberColumn(format='dollar', width=60)
                        }
                        )
                    st.info(':material/lightbulb: Al dar click en :red[Eliminar] ' \
                    'los cambios no pueden deshacercerse :material/lightbulb:')

                    eliminar_seleccionados = st.button(
                        label=':material/delete: Eliminar Seleccionados',
                        key='eliminar_seleccionados',
                        type='primary'
                        )
                    
                    if eliminar_seleccionados:
                        # Basado en los indices seleccionados por el usuario elimino las filas en el df original
                        copia = copia[copia['Producto'].isin(seleccion_eliminar)]
                        df = df.drop(index=copia.index)
                        # Creo el diccionario que se guardara en json:
                        data = df.to_dict(orient='list')
                        # Guardo los cambio: Parseo el diccionario a json
                        with open(RUTA, 'w', encoding='utf-8') as e:
                            json.dump(data, e,indent=4, ensure_ascii=False)

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
    
    st.subheader(':material/barcode_scanner: Ajustar Cantidad Con Scanner')
    df = lectura_del_inventario()
    try:
        
        df.set_index('Codigo',inplace=True)
        
        copy = df.copy()
        copy['Cantidad Actual'] = df['Cantidad']
        copy['Nueva Cantidad'] = 0
        OPCIONES = df.index.tolist()
        
        escaner = st.multiselect(
            label='Escanea Los Codigos Deseados',
            options=OPCIONES
        )
        
        if escaner:
            salida = st.data_editor(
                data=copy[copy.index.isin(escaner)],
                column_order=['Producto','Cantidad Actual','Nueva Cantidad'],
                column_config={
                    '_index':st.column_config.NumberColumn(disabled=True),
                    'Producto':st.column_config.TextColumn(disabled=True),
                    'Cantidad Actual':st.column_config.NumberColumn(disabled=True)
                }
            )

            guardar = st.button(
                label='Guardar Cambios',
                type='primary',
                key='guardar_cambios'
            )

            if guardar:
                salida.reset_index(inplace=True)
                df.loc[df.index.isin(salida['Codigo']),'Cantidad'] = salida['Nueva Cantidad'].values
                df.reset_index(inplace=True)
                df = df[[
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
                datos = df.to_dict(orient='list')
                with open(RUTA,'w',encoding='utf-8')as e:
                    json.dump(datos,e,indent=4,ensure_ascii=False)
                st.success('Datos Ajustados Correctamente')
                st.stop()
    except st.errors.StreamlitAPIException:
        st.info('Agregue Entradas Al Inventario')

def crear_etiquetas_codigo():
    """" Es codigo genera codigos de barras y sus etiquetas para ser descargados"""
    st.subheader(':material/label: Imprime Etiquetas Para Tu Inventario')
    try:
        # Leo los datos desde la base de datos y los cargo a un DataFrame
        if os.path.exists(RUTA) and os.path.getsize(RUTA) > 0:
            with open(RUTA,'r',encoding='utf-8') as f:
                df = pd.DataFrame(data=json.load(f))

            # Preparo las columnas que utilizare:
            df['Codigo'] = df['Codigo'].astype('str')

            st.info('Si deseas todas las etiquetas no ingreses valores en la "Barra De Busqueda".')
            # Opcion de filtro y crear etiquetas para la interfaz de usuario:
            seleccion_especifica = st.multiselect(
                label='Selecciona Las Etiquetas Deseadas',
                key='seleccion_especifica',
                options=df['Producto'].tolist()
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
                    df = df[df['Producto'].isin(seleccion_especifica)]

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
                        box_size = draw.textbbox((0,0),row['Producto'],font=font_path_nombre)
                        p_x = box_size[2] - box_size[0]
                        p_y = box_size[3] - box_size[1]
                        x_producto = (LABEL_WIDTH - p_x) // 2
                        y_producto = ((LABEL_HEIGHT - p_y) // 2) - 80
                        draw.text((x_producto,y_producto ), row['Producto'], font=font_path_nombre, fill='black')

                        img_buffer=io.BytesIO()
                        etiqueta_img.save(img_buffer,format='PNG')
                        img_buffer.seek(0)

                        nombre_limpio = row['Producto'].replace('/','-').replace('(','').replace(')','')
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
st.header(f':material/inventory_2: {l.phrase[2]}')

seleccion_inventario_opciones = st.pills(
    key='agregar_entrada_al_inventario',
    label='',
    options=[
        f':material/inventory_2: {l.phrase[2]}',
        ':material/docs_add_on: Agregar Nuevo Registro',
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
    
if seleccion_inventario_opciones == ':material/docs_add_on: Agregar Nuevo Registro':
    formulario_entrada_catalogo()

if seleccion_inventario_opciones == ':material/table_edit: Ajuste Simple':
    ajustar_inventario()

if seleccion_inventario_opciones == ':material/delete: Eliminar Producto':
    eliminar_entradas()

if seleccion_inventario_opciones == ':material/barcode_scanner: Ajustar Producto Con Scaner':
    ajustar_por_codigo()

if seleccion_inventario_opciones == ':material/label: Imprimir Etiquetas de Codigo':
    crear_etiquetas_codigo()