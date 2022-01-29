from re import X
import streamlit as st
import os
import datetime
import base64
import geemap as gee
import pandas as pd
from imagery import Imagery
from map import map_component

# page config
st.set_page_config(page_title="SARveillance", page_icon="🛰️")

class SARVEILLANCE():

  def __init__(self):
    self.gee = gee
    self.bases = []
    self.poi = {}
    self.start_date = None
    self.end_date = None
    self.imagery = None
    # ugly attempt to get the data folder path
    self.outpath = os.path.abspath(os.path.join(__file__, '..', '..', 'data'))
    self.max_frames=30

  def run(self):
    self.setup_gee()
    self.bases = self.load_bases()
    self.init_imagery()
    self.init_gui()

  def setup_gee(self):
    # self.gee.ee.Authenticate()
    self.gee.ee_initialize()

  @st.cache
  def load_bases(self):
    '''
    Loads the base data into a pandas dataframe
    Uses st.cache (with disabled warning) to only load once
    '''
    return pd.read_csv("poi/poi_df.csv")

  def init_imagery(self):
    self.imagery = Imagery()
    self.imagery.get_collection()

  def is_name_in_preset(self, name):
    '''
    checks if <name> is in the poi dataframe
    '''
    check = self.bases.loc[self.bases['Name'] == name]
    return not check.empty

  def get_preset_from_name(self, name):
    preset_data = self.bases.loc[self.bases['Name'] == name]
    if not preset_data.empty:
      name = preset_data['Name'].values[0]
      lat = preset_data['lat'].values[0]
      lon = preset_data['lon'].values[0]
      return (False, (name, lat, lon))
    else:
      return (True, 'Location not found in preset data')

  def generate_poi(self, state):
    error = False # default
    msg = ''
    needed_fields = ['name', 'lat', 'lon', 'start_date', 'end_date']
    for field in needed_fields:
      if state[field] and state[field] != '':
        self.poi[field] = state[field]
        # special stuff
        if field == 'lat' or field == 'lon':
          try:
            float(state[field])
          except ValueError:
            error = True
            msg = 'Latitude & Longitude must be numeric values!'
            break
          else:
            self.poi[field] = float(state[field])
        if field == 'start_date' or field == 'end_date':
          self.poi[field] = state[field].isoformat()
      else:
        error = True
        msg = 'Choose a location!'
        break

    return (error, msg)

  # @st.cache(suppress_st_warning=True)
  def load_custom_css(self):
    '''
    Loads the custom css and inserts the style into the page
    Uses st.cache (with disabled warning) to only load once
    '''
    with open('app/custom.css') as f:
      st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

  def init_gui(self):
    # load custom css
    self.load_custom_css()

    # prepare initial form data
    poi_list = self.bases['Name'].tolist()
    poi_list.insert(0, '---')

    # header
    st.title('SARveillance')
    st.subheader('Sentinel-1 SAR time series analysis for OSINT use')

    # Initialization of session state
    if 'name' not in st.session_state:
      st.session_state.name = ''
    if 'lat' not in st.session_state:
      st.session_state.lat = '' # default location
    if 'lon' not in st.session_state:
      st.session_state.lon = '' # default location
    if 'is_custom' not in st.session_state:
      st.session_state.is_custom = False
    if 'inputs_disabled' not in st.session_state:
      st.session_state.inputs_disabled = True
    if 'map' not in st.session_state:
      st.session_state.map = 'init'
    if 'allow_click' not in st.session_state:
      st.session_state.allow_click = False

    # preset poi on change
    def on_select():
      (err, msg) = self.get_preset_from_name(st.session_state.poi_select)
      if not err:
        (name, lat, lon) = msg
        st.session_state.name = name
        st.session_state.lat = str(lat)
        st.session_state.lon = str(lon)

    def on_checkbox():
      st.session_state['inputs_disabled'] = not st.session_state.is_custom
      st.session_state.allow_click = st.session_state.is_custom

    def on_latlon():
      pass
      # print('on latlon')

    def on_name():
      pass
      # print('on name')

    # preset poi selectbox
    st.selectbox('Preset Location', poi_list, key='poi_select', on_change=on_select)

    # checkbox to switch between preset and custom location
    st.checkbox('Custom location (Click on the map and enter a name)', key='is_custom', on_change=on_checkbox)

    # define the form via st.empty() first, so you can update it later more easily
    col_name, col_lat, col_lon = st.columns(3)
    with col_name:
      name_container = st.empty()
    with col_lat:
      lat_container = st.empty()
    with col_lon:
      lon_container = st.empty()

    # inputs for name, lat & lon
    custom_name = name_container.text_input('Name (required)', key='name', disabled=st.session_state.inputs_disabled, on_change=on_name)
    lat = lat_container.text_input('Latitude (required)', key='lat', disabled=st.session_state.inputs_disabled, on_change=on_latlon)
    lon = lon_container.text_input('Longitude (required)', key='lon', disabled=st.session_state.inputs_disabled, on_change=on_latlon)

    # call map component and watch for return values
    # if we already have coordinates, use them to display a marker
    payload = { 'lat': lat, 'lon': lon, 'is_custom': st.session_state.allow_click }
    map_component(payload=payload, key='map')
    # if map component returns coordinates
    # we update the input fields
    if st.session_state.map != 'init':
      # update name field only if current name is in preset
      # defaults to 'Custom'
      if self.is_name_in_preset(st.session_state.name) or st.session_state.name == '':
        custom_name = name_container.text_input('Name (required)', key='name', value='Custom', disabled=st.session_state.inputs_disabled, on_change=on_name)
      # update the lat, lon inputs with the new values from the map click
      (map_lat, map_lon) = st.session_state.map
      lat = lat_container.text_input('Latitude (required)', key='lat', value=map_lat, disabled=st.session_state.inputs_disabled, on_change=on_latlon)
      lon = lon_container.text_input('Longitude (required)', key='lon', value=map_lon, disabled=st.session_state.inputs_disabled, on_change=on_latlon)


    # date picker for start & end date (form element)
    today = datetime.date.today()
    lastweek = (today - datetime.timedelta(days=7))
    col_start_date, col_end_date = st.columns(2)
    with col_start_date:
      start_date = st.date_input('Start Date', value=lastweek, key='start_date')
    with col_end_date:
      end_date = st.date_input('End Date', value=today, key='end_date')
    # format the dates and set class variables
    start_date = start_date.isoformat()
    end_date = end_date.isoformat()

    # gather all data
    (err, msg) = self.generate_poi(st.session_state)
    if (err):
      st.error(msg)
      st.stop()
    else:
      st.markdown(f"<div class='st-ae st-af st-ag st-ah st-ai st-aj st-ak st-al st-am st-b8 st-ao st-ap st-aq st-ar st-as st-at st-au st-av st-aw st-ax st-ay st-az st-b9 st-b1 st-b2 st-b3 st-b4 st-b5 st-b6' style='flex-direction: column;'><h6>Location: {st.session_state.name}</h6>Coordinates: [{st.session_state.lat}, {st.session_state.lon}]<br />Timespan: {st.session_state.start_date} - {st.session_state.end_date}</div><br />", unsafe_allow_html=True)

      # on submit
      if st.button('Generate SAR Timeseries'):
        pass
        self.generate()


  def generate(self):
    with st.spinner('Loading timeseries... this may take a couple of minutes'):
      self.imagery.set_poi(self.poi, self.outpath)
      (err, msg) = self.imagery.generate_timeseries_gif(max_frames=self.max_frames)

    if err:
      st.error(msg)
      st.stop()
    else:
      st.success('Done!')
      self.display_gif()
      self.show_download()

  def display_gif(self):
    # poi data
    base_name = self.poi['name']
    base_path = os.path.join(self.outpath, 'BaseTimeseries', base_name)
    if not os.path.exists(base_path):
      os.makedirs(base_path)
    gif_loc = f'{base_path}/{base_name}.gif'
    file_ = open(gif_loc, "rb")
    contents = file_.read()
    data_url = base64.b64encode(contents).decode("utf-8")
    file_.close()
    st.markdown(
    f'<img align="left" width="704" height="704" src="data:image/gif;base64,{data_url}" alt="Base Timeseries">',
    unsafe_allow_html=True)

  def show_download(self):
    # poi data
    base_name = self.poi['name']  
    base_path = os.path.join(self.outpath, 'BaseTimeseries', base_name)
    if not os.path.exists(base_path):
      os.makedirs(base_path) 
    gif_loc = f'{base_path}/{base_name}.gif'

    with open(gif_loc, "rb") as file:
      btn = st.download_button(
        label="Download image",
        data=file,
        file_name="timeseries.gif",
        mime="image/gif"
        )


if __name__ == '__main__':
  # overwrite cartoee method 
  # cartoee.get_image_collection_gif = new_get_image_collection_gif
  # start a new class instance with the run() method
  sar = SARVEILLANCE()
  sar.run()