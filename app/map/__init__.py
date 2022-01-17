import streamlit.components.v1 as components
_component_func = components.declare_component(
    name='map_component',
    path='./app/map'
)

# component wrapper, to allow arguments
def map_component(payload=None, key=None):
    return _component_func(payload=payload, key=key, default=0)