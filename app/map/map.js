// constants
const SET_COMPONENT_VALUE = 'streamlit:setComponentValue';
const RENDER = 'streamlit:render';
const COMPONENT_READY = 'streamlit:componentReady';
const SET_FRAME_HEIGHT = 'streamlit:setFrameHeight';

class Map {
  constructor() {
    this.map = null;
    this.layerGroup = null;
    this.is_custom = false
  }

  sendMessage(type, data) {

    // copy data into object
    var outboundData = Object.assign(
      {
        isStreamlitMessage: true,
        type: type,
      },
      data
    );
  
    // debug
    // if (type == SET_COMPONENT_VALUE) {
    //   console.log('_sendMessage data: ' + JSON.stringify(data));
    //   console.log('_sendMessage outboundData: ' + JSON.stringify(outboundData));
    // }

    // send postmsg to parent  
    window.parent.postMessage(outboundData, '*');
  }

  initialize() {

    // Hook Streamlit's message events into a simple dispatcher of pipeline handlers
    window.addEventListener('message', (event) => {
      if (event.data.type == RENDER) {
        const payload = event.data.args.payload;
        const {lat, lon, is_custom} = payload;
        this.is_custom = is_custom;
        if (lat !== '' && lon !== '') {       
          this.layerGroup.clearLayers();
          L.marker([lat, lon]).addTo(this.layerGroup);
          L.circle([lat, lon], { radius: 4000, color: '#ff0000', weight: 1, fillOpacity: 0.1 }).addTo(this.layerGroup);
          this.map.setView([lat, lon]);
        }
      }
    });

    // notify streamlit that component is ready
    this.sendMessage(COMPONENT_READY, { apiVersion: 1 });
 
    // Component should be mounted by Streamlit in an iframe, so try to autoset the iframe height.
    window.addEventListener('load', () => {
      window.setTimeout(() => {
        this.setFrameHeight(document.documentElement.clientHeight);
      }, 0);
    });
  }

  setFrameHeight(height) {
    this.sendMessage(SET_FRAME_HEIGHT, { height: height });
  }


  // The `data` argument can be any JSON-serializable value.
  notifyHost(data) {
    // console.log('Send data back:', data)
    this.sendMessage(SET_COMPONENT_VALUE, data);
  }

  // create map
  create() {

    // console.log('init map');

    // init map with default coordinates + zoom level
    // this.map = L.map('map').setView([0, 0], 5);
    this.map = L.map('map').setView([51.004, 37.111], 5);

    // osm layer (topo)
    const osm = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      attribution:
        '&copy; <a href="https://openstreetmap.org/copyright">OpenStreetMap contributors</a>',
    });

    // esri layer (sat)
    const esri = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
    attribution: 'Powered by <a href="https://www.esri.com/">Esri</a>'
    });

    // combine the layers
    const baseMaps = {
      "OpenStreetMap": osm,
      "EsriWorldImagery": esri
    };

    // set default layer
    osm.addTo(this.map);

    // add layer control (default: topright)
    L.control.layers(baseMaps).addTo(this.map);

    // show the scale bar on the lower left corner
    L.control.scale({ imperial: true, metric: true, position: 'bottomleft' }).addTo(this.map);
  
    // add a layergroup which holds (all) the marker
    // we use this to later remove all markers previously set
    this.layerGroup = L.layerGroup().addTo(this.map);
  
    // onclick
    this.map.on('click', (ev) => {

      if(!this.is_custom) {
        return;
      }

      // clear all old markers
      this.layerGroup.clearLayers();

      // get the coordinates
      const latlon = this.map.mouseEventToLatLng(ev.originalEvent);

      // point
      const point = [latlon.lat, latlon.lng];

      // add a marker with these coordinates
      L.marker(point).addTo(this.layerGroup);

      // circle
      L.circle(point, { radius: 4000, color: '#ff0000', weight: 1, fillOpacity: 0.1 }).addTo(this.layerGroup);

      // center map on marker
      this.map.setView(point);

      // notify streamlit with the new set of coordinates
      this.notifyHost({
        value: point,
        dataType: 'json',
      });

    });

    this.initialize();

  }

}


(function () {
  const map = new Map();
  map.create();
  // map.initialize();
} () );
