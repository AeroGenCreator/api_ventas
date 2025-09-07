import streamlit as st

import lenguaje

l = lenguaje.tu_idioma()

st.title(l.phrase[5])