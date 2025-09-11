import lenguaje

import streamlit as st

l = lenguaje.tu_idioma()
st.title(l.phrase[0])

# Esto se eliminara despues
import streamlit as st
from streamlit_scanner_component import scanner_component

st.title('Prueba')

texto_escaneado = scanner_component()

st.write(texto_escaneado)

