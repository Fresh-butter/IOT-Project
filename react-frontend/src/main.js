import L from 'leaflet';
import 'leaflet.markercluster';
import 'leaflet/dist/leaflet.css';

// Initialize the map
const map = L.map('map').setView([20.5937, 78.9629], 5); // Centered on India
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
  attribution: '&copy; OpenStreetMap contributors',
}).addTo(map);

const markers = L.markerClusterGroup();
map.addLayer(markers);

// Function to fetch train data
async function fetchTrainData() {
  const loader = document.getElementById('loader');
  loader.style.display = 'flex'; // Show loader

  try {
    const response = await fetch('https://iot-project-c3wb.onrender.com'); // Replace with actual API URL
    const data = await response.json();

    // Clear existing markers
    markers.clearLayers();

    // Add markers to the map
    data.trains.forEach((train) => {
      const marker = L.marker([train.latitude, train.longitude]);
      marker.bindPopup(`<b>${train.name}</b><br>Speed: ${train.speed} km/h`);
      markers.addLayer(marker);
    });
  } catch (error) {
    console.error('Error fetching train data:', error);
    alert('Failed to fetch train data. Please try again later.');
  } finally {
    loader.style.display = 'none'; // Hide loader
  }
}

// Initial data fetch
fetchTrainData();

// Function to refresh data
window.refreshData = fetchTrainData;
