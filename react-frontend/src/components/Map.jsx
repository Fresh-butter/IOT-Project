import React, { useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';

const Map = () => {
  const trainPositions = [
    { id: 1, lat: 51.505, lng: -0.09, name: 'Train 1' },
    { id: 2, lat: 51.515, lng: -0.1, name: 'Train 2' },
  ];

  return (
    <div className="h-96 w-full">
      <MapContainer center={[51.505, -0.09]} zoom={13} className="h-full w-full">
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution="&copy; OpenStreetMap contributors"
        />
        {trainPositions.map((train) => (
          <Marker key={train.id} position={[train.lat, train.lng]}>
            <Popup>{train.name}</Popup>
          </Marker>
        ))}
      </MapContainer>
    </div>
  );
};

export default Map;
