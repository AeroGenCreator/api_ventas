"""Este archivo controla el flujo de navegacion de la aplicacion, todas las paginas
de la API se encuentran aqui"""

# Python Librerias
import yaml
from yaml.loader import SafeLoader

# Mis modulos
import lenguaje

# 3ros Librerias
import streamlit as st
import streamlit_authenticator as stauth

l=lenguaje.tu_idioma()

with open('credentials.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days']
)

try:
    login = authenticator.login(location='main')
except Exception as e:
    st.error(e)

if st.session_state.get('authentication_status') is False:
    st.error('Error Contraae;a Passsword')

if st.session_state.get('authentication_status') is None:
    st.warning('Ingresa u y pass')

elif st.session_state.get('authentication_status'):
    authenticator.logout(location='sidebar', button_name='Cerrrar Sesion')
    
    st.sidebar.subheader(f'Bienvenido :orange[{st.session_state.get('name')}]')
    
    iterable_pages = [
    st.Page(page='inicio.py', title=l.phrase[0], icon=':material/store:'),
    st.Page(page='vender.py', title=l.phrase[1], icon=':material/sell:'),
    st.Page(page='inventario.py', title=l.phrase[2], icon=':material/inventory_2:'),
    st.Page(page='cotizacion.py', title=l.phrase[3], icon=':material/request_quote:'),
    st.Page(page='historial.py', title=l.phrase[4], icon=':material/history:'),
    st.Page(page='estadisticas.py', title=l.phrase[5], icon=':material/analytics:'),
    st.Page(page='config.py', title=l.phrase[6], icon=':material/settings:')
    ]

    to_run = st.navigation(pages=iterable_pages, position='sidebar')

    to_run.run()


