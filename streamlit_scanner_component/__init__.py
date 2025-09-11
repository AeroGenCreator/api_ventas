import streamlit.components.v1 as components
import os

_RELEASE = False

if not _RELEASE:
    _component_func = components.declare_component(
        'my_scanner',
        url="http://127.0.0.1:5500"
    )
else:
    parent_dir = os.path.dirname(os.path.abspath(__file__))
    build_dir = os.path.join(parent_dir,'frontend')
    _component_func = components.declare_component('my_scanner', path=build_dir)

def scanner_component():
    return _component_func()