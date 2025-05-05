import { MapContainer, TileLayer, Marker, Popup, Polyline } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import { Route } from '../services/api';
import { Box, Paper, Typography } from '@mui/material';

// Fix default icon issue in Leaflet
delete (L.Icon.Default.prototype as { _getIconUrl?: () => string })._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-shadow.png',
});

interface RouteMapProps {
  selectedRoute: Route | null;
}

const RouteMap: React.FC<RouteMapProps> = ({ selectedRoute }) => {
  // Default center (India)
  const defaultCenter: [number, number] = [20.5937, 78.9629];
  const defaultZoom = 5;

  if (!selectedRoute) {
    return (
      <Paper 
        elevation={3} 
        sx={{ 
          height: '500px', 
          display: 'flex', 
          justifyContent: 'center', 
          alignItems: 'center',
          bgcolor: '#f5f5f5'
        }}
      >
        <Typography variant="h6" color="text.secondary">
          Select a route to view on map
        </Typography>
      </Paper>
    );
  }

  // Get route checkpoints
  const checkpoints = selectedRoute.checkpoints;
  
  // Create line for route - no need to swap coordinates if your API already uses [lat, lon]
  const routeLine = checkpoints.map(checkpoint => checkpoint.location);

  // Get center from first checkpoint or use default
  const center: [number, number] = checkpoints.length > 0 
    ? checkpoints[0].location
    : defaultCenter;
  
  // Calculate appropriate zoom level
  const zoom = checkpoints.length > 0 ? 8 : defaultZoom;
  
  return (
    <Paper elevation={3} sx={{ height: '500px', border: '1px solid #e0e0e0' }}>
      <MapContainer 
        center={center} 
        zoom={zoom} 
        style={{ height: '100%', width: '100%' }}
      >
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        />
        
        {/* Draw the route line */}
        {routeLine.length > 1 && (
          <Polyline 
            positions={routeLine} 
            color="#3388ff" 
            weight={4} 
            opacity={0.8}
          />
        )}
        
        {/* Place markers at each checkpoint */}
        {checkpoints.map((checkpoint, index) => (
          <Marker 
            key={index} 
            position={checkpoint.location}
          >
            <Popup>
              <Box>
                <Typography variant="subtitle2">
                  {checkpoint.name || `Checkpoint ${index + 1}`}
                </Typography>
                {checkpoint.rfid_tag && (
                  <Typography variant="body2">
                    RFID: {checkpoint.rfid_tag}
                  </Typography>
                )}
                <Typography variant="body2">
                  Interval: {Math.floor(checkpoint.interval / 60)} minutes
                </Typography>
                <Typography variant="body2">
                  Location: [{checkpoint.location[1].toFixed(4)}, {checkpoint.location[0].toFixed(4)}]
                </Typography>
              </Box>
            </Popup>
          </Marker>
        ))}
      </MapContainer>
    </Paper>
  );
};

export default RouteMap;