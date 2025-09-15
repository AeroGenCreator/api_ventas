"""En este archivo se accede a las opciones de configuracion
y se editan las mismas para posteriormente ser almacenadas en 
el archivo configuraciones_file.json"""

# Mis modulos
import lenguaje
# Terceros librerias
import streamlit as st

l=lenguaje.tu_idioma()
st.header(f':material/settings: {l.phrase[6]}')

# Aqui accedo a los archivos de lenguaje.py, creo un widget de seleccion de idioma
# El selector, guarda los cambio en configuracion_file.json
# Para conocer el proceso, estudiar el codigo del archivo lenguaje.py
seleccion_idioma = lenguaje.escojer_idioma(llave='seleccion_configuracion')
# Aqui se leen los datos de configuracion_file.json/configuracion/idioma
# Y se leen los datos de configuracion_file.json/configuracion/traducciones
# Se crea un objeto con las traducciones disponibles y accedo a cada frase guardada
# utilizando el atributo .phrase[] y un indice dentro de los corchetes de barra.
l = lenguaje.tu_idioma()

guardar_cambios = st.button(
    label='guardar cambios',
    key='guardar_cambios',
    )

st.write('ID vendedor/ID Fabricante para usb scanner')

if guardar_cambios:
    st.rerun()

# Esto se eliminara despues
import streamlit as st
from streamlit_scanner_component import scanner_component

st.title('Prueba')
texto_escaneado = scanner_component()
st.write(texto_escaneado)

