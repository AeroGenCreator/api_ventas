import streamlit as st
import json
import os

PATH_CONFIGURACION = 'configuracion_file.json'

idiomas={
    'Español':[],
    'English':[]
}

class language:

    def __init__(self, lista_escogida:list):
        self.phrase = lista_escogida

def escojer_idioma(llave:str):
    if os.path.exists(PATH_CONFIGURACION) and os.path.getsize(PATH_CONFIGURACION) > 0:
        with open(PATH_CONFIGURACION, 'r', encoding='utf-8') as r:
            datos = json.load(r)
            default_option = datos['configuracion']['idioma']
    else:
        default_option = 'Español'
    
    opciones = idiomas.keys()

    choice = st.pills(
        label=':material/language: Language',
        options=opciones,
        default=default_option,
        key=llave
    )

    if os.path.exists(PATH_CONFIGURACION) and os.path.getsize(PATH_CONFIGURACION) > 0:
        with open(PATH_CONFIGURACION, 'r', encoding='utf-8') as r:
            datos = json.load(r)
            datos['configuracion']['idioma'] = choice
        with open(PATH_CONFIGURACION, 'w', encoding='utf-8') as e:
            json.dump(datos, e, indent=4, ensure_ascii=False)
    
    else:
        with open(PATH_CONFIGURACION, 'w', encoding='utf-8') as f:
            creacion = {
                'configuracion':{
                    'idioma': choice,
                    'traducciones':idiomas
                    }
                }
            json.dump(creacion, f, indent=4, ensure_ascii=False)
    return choice

def tu_idioma():
    with open(PATH_CONFIGURACION, 'r', encoding='utf-8') as r:
        datos = json.load(r)
        idioma_seleccionado = datos['configuracion']['idioma']
        lista_escogida = datos['configuracion']['traducciones'][idioma_seleccionado]
        traduccion = language(lista_escogida)
        return traduccion