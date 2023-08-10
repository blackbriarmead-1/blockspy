import React, {useState} from "react";
import { MapContainer, TileLayer, Marker, Popup, ZoomControl, ScaleControl } from 'react-leaflet';
import './App.css';
import { Icon } from "leaflet";
import './leaflet.css';

const s = 50
const mapBounds = [
  [-2*s,s],
  [2*s,-s],
]

const centerPos = [36.54, -39.4]
const zoom = 5
const zoom_offset = -2
function App() {
  return (
    <MapContainer bounds={mapBounds} center={[36.5,-39]} scrollWheelZoom={true} style={{ height: '100vh', width: '100wh' }} zoom={zoom-zoom_offset}>
      <TileLayer
        url="http://127.0.0.1:5000/tile?x={x}&y={y}&zoom={z}&index=-1"
        maxNativeZoom={zoom-zoom_offset}
        minNativeZoom={zoom-zoom_offset}
        noWrap={true}
        tileSize={512}
        zoomOffset={zoom_offset}

      />
      <ScaleControl/>
    </MapContainer>
  );
}

export default App;