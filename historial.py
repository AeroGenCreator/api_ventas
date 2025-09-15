import json

import lenguaje
from vender import acceso_a_historial

import streamlit as st
import pandas as pd

l=lenguaje.tu_idioma()

st.title(l.phrase[4])

data = acceso_a_historial()
st.dataframe(data=data,hide_index=True)