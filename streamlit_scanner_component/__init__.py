import streamlit.components.v1 as components
import os

_RELEASE = True

if not _RELEASE:
    # La URL debe apuntar a la base de la carpeta frontend
    _component_func = components.declare_component(
        'my_scanner',
        url="http://127.0.0.1:5500/streamlit_scanner_component/frontend" # <-- URL corregida
    )
else:
    # El modo de producción ya usa el path correcto
    parent_dir = os.path.dirname(os.path.abspath(__file__))
    build_dir = os.path.join(parent_dir, "frontend")
    _component_func = components.declare_component("my_scanner", path=build_dir)

def scanner_component():
    return _component_func()