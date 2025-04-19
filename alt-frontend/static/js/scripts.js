// Initialize the map using Leaflet.js
function initMap(trains) {
    const map = L.map('map').setView([12.9716, 77.5946], 10); // Initial map center
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 18,
        attribution: '© OpenStreetMap'
    }).addTo(map);

    // Add markers for each train
    trains.forEach(train => {
        const marker = L.marker([train.latitude, train.longitude]).addTo(map);
        marker.bindPopup(`<b>${train.name}</b><br>Lat: ${train.latitude}, Lng: ${train.longitude}`);
    });
}

// Render speed graph using Chart.js
function renderSpeedGraph(trains) {
    const ctx = document.getElementById('speedChart').getContext('2d');
    const labels = trains.map(train => train.name);
    const data = trains.map(train => train.speed);

    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Speed (km/h)',
                data: data,
                backgroundColor: 'rgba(75, 192, 192, 0.2)',
                borderColor: 'rgba(75, 192, 192, 1)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}

// Fetch data from the backend and initialize widgets
document.addEventListener('DOMContentLoaded', () => {
    fetch('/api/data') // Adjust this endpoint as needed
        .then(response => response.json())
        .then(data => {
            initMap(data.trains);
            renderSpeedGraph(data.trains);
        });
});
