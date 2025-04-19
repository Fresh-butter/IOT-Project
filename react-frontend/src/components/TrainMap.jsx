// TrainMap.jsx
import { MapContainer, TileLayer, Marker, Polyline } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';

L.Icon.Default.mergeOptions({
    iconRetinaUrl: '/assets/marker-icon-2x.png',
    iconUrl: '/assets/marker-icon.png',
    shadowUrl: '/assets/marker-shadow.png',
});

const TrainMap = () => {
  const center = [17.445405055968216, 78.34931177070476]; // Change to your region
  const zoom = 50;

  // Example route (latitude, longitude points for polyline)
  const route = [
    [28.6139, 77.2090], // Delhi
    [28.4089, 77.3178], // Faridabad
    [27.1767, 78.0081], // Agra
  ];

  return (
    <MapContainer center={center} zoom={zoom} style={{ height: '500px', width: '100%' }}>
      <TileLayer
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />

      {/* Route Line */}
      <Polyline positions={route} color="red" />
      
       <Marker position={center} />

      {/* Start & End Markers */}
      <Marker position={route[0]} />
      <Marker position={route[route.length - 1]} />
    </MapContainer>
  );
};

export default TrainMap;