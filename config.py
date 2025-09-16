"""En este archivo se accede a las opciones de configuracion
y se editan las mismas para posteriormente ser almacenadas en 
el archivo configuraciones_file.json"""
import os
import json
# Mis modulos
import lenguaje
# Terceros librerias
import streamlit as st

RUTA_CONFIG = 'configuracion_file.json'

def acceso_fondo_caja():
    
    try:
        if os.path.exists(RUTA_CONFIG) and os.path.getsize(RUTA_CONFIG) > 0:
            with open(RUTA_CONFIG,'r',encoding='utf-8') as f:
                datos = json.load(f)   
                return datos['configuracion']['caja fondo']
        else:
            st.warning(f'1. No se encuentra o se altero el archivo {RUTA_CONFIG}. Pedir ayuda con el soporte')
    except (FileNotFoundError,FileExistsError,json.JSONDecodeError):
        st.warning(f'2. No se encuentra o se altero el archivo <{RUTA_CONFIG}> Pedir ayuda con el soporte')

def cambiar_fondo(cantidad):
    try:
        if os.path.exists(RUTA_CONFIG) and os.path.getsize(RUTA_CONFIG) > 0:
            with open(RUTA_CONFIG,'r',encoding='utf-8') as f:
                datos = json.load(f)   
                datos['configuracion']['caja fondo'] = cantidad
            with open(RUTA_CONFIG,'w',encoding='utf-8') as e:
                json.dump(datos,e,indent=4,ensure_ascii=False)
        else:
            st.warning(f'1. No se encuentra o se altero el archivo {RUTA_CONFIG}. Pedir ayuda con el soporte')
    except (FileNotFoundError,FileExistsError,json.JSONDecodeError):
        st.warning(f'2. No se encuentra o se altero el archivo <{RUTA_CONFIG}> Pedir ayuda con el soporte')

l=lenguaje.tu_idioma()
st.header(f':material/settings: {l.phrase[6]}')

# AQUI COMIENZA LA INTERFAZ --------------------------------------------------------------------------------------------------------

# Aqui accedo a los archivos de lenguaje.py, creo un widget de seleccion de idioma
# El selector, guarda los cambio en configuracion_file.json
# Para conocer el proceso, estudiar el codigo del archivo lenguaje.py
seleccion_idioma = lenguaje.escojer_idioma(llave='seleccion_configuracion')
# Aqui se leen los datos de configuracion_file.json/configuracion/idioma
# Y se leen los datos de configuracion_file.json/configuracion/traducciones
# Se crea un objeto con las traducciones disponibles y accedo a cada frase guardada
# utilizando el atributo .phrase[] y un indice dentro de los corchetes de barra.
l = lenguaje.tu_idioma()
st.divider()

st.write(f'Tu Fondo de Caja: :red[{acceso_fondo_caja()}]')
fondo = st.number_input(
    label='Ingresa Una Nueva Cantidad - Guarda los Cambios',
    step=1,
    min_value=0
    )
if fondo:
    cambiar_fondo(fondo)
st.divider()

# Esto se eliminara despues
import streamlit as st
from streamlit_scanner_component import scanner_component

st.title('Prueba')
texto_escaneado = scanner_component()
st.write(texto_escaneado)

guardar_cambios = st.button(
    label='Guardar Cambios',
    key='guardar_cambios',
    )
if guardar_cambios:
    st.rerun()