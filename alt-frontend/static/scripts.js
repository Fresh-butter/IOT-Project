// scripts.js

// Initialize a map (example using Leaflet.js)
function initMap(trains) {
    const map = L.map('map').setView([12.9716, 77.5946], 10); // Initial map center and zoom level

    // Add OpenStreetMap tiles
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 18,
        attribution: '© OpenStreetMap'
    }).addTo(map);

    // Add train markers
    trains.forEach(train => {
        const marker = L.marker([train.latitude, train.longitude]).addTo(map);
        marker.bindPopup(`<b>${train.name}</b><br>Lat: ${train.latitude}, Lng: ${train.longitude}`);
    });
}

// Update map markers (example for real-time data)
function updateMap(map, trains) {
    map.eachLayer(layer => {
        if (layer instanceof L.Marker) {
            map.removeLayer(layer);
        }
    });

    trains.forEach(train => {
        const marker = L.marker([train.latitude, train.longitude]).addTo(map);
        marker.bindPopup(`<b>${train.name}</b><br>Lat: ${train.latitude}, Lng: ${train.longitude}`);
    });
}

// Alarm Widget: Show alerts
function updateAlarmWidget(trains) {
    trains.forEach(train => {
        const alertElement = document.getElementById(`alert-${train.name}`);
        if (train.alert === 1) {
            alertElement.style.color = 'red';
            alertElement.textContent = `${train.name}: Danger!`;
        } else {
            alertElement.style.color = 'green';
            alertElement.textContent = `${train.name}: Safe`;
        }
    });
}

// Speed Widget: Render speed graph (optional, using Chart.js)
function renderSpeedGraph(trainSpeeds) {
    const ctx = document.getElementById('speedChart').getContext('2d');
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: trainSpeeds.timestamps, // Array of timestamps
            datasets: trainSpeeds.trains.map(train => ({
                label: train.name,
                data: train.speeds, // Array of speed values
                borderColor: getRandomColor(),
                fill: false
            }))
        },
        options: {
            responsive: true,
            title: {
                display: true,
                text: 'Train Speed Over Time'
            },
            scales: {
                x: {
                    type: 'time',
                    time: {
                        unit: 'minute'
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: 'Speed (km/h)'
                    },
                    beginAtZero: true
                }
            }
        }
    });
}

// Helper function to get random colors for graphs
function getRandomColor() {
    const letters = '0123456789ABCDEF';
    let color = '#';
    for (let i = 0; i < 6; i++) {
        color += letters[Math.floor(Math.random() * 16)];
    }
    return color;
}

// Example: Mock data for initializing widgets
document.addEventListener('DOMContentLoaded', () => {
    const trains = [
        { name: 'Train A', latitude: 12.9716, longitude: 77.5946, alert: 0 },
        { name: 'Train B', latitude: 12.2958, longitude: 76.6394, alert: 1 }
    ];

    initMap(trains);
    updateAlarmWidget(trains);

    // Example: Mock data for speed graph
    const trainSpeeds = {
        timestamps: ['2025-04-19T13:00:00', '2025-04-19T13:10:00', '2025-04-19T13:20:00'],
        trains: [
            { name: 'Train A', speeds: [80, 85, 90] },
            { name: 'Train B', speeds: [100, 95, 110] }
        ]
    };
    renderSpeedGraph(trainSpeeds);
});
