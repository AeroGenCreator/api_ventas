import streamlit as st

import lenguaje

l = lenguaje.tu_idioma()

st.header(f':material/analytics: {l.phrase[5]}')