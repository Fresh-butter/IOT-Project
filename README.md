GPS & RFID-Based Train Collision Avoidance System
Overview

This project is a GPS & RFID-Based Train Collision Avoidance System using ESP32, GPS modules, and RFID technology. The system prevents train collisions by detecting train positions and exchanging data between ESP32 devices, a cloud-hosted backend, and a web-based dashboard.
Technologies Used
Frontend

    React.js (with Vite) - For building the web dashboard.

    Tailwind CSS - For styling.

    Leaflet.js / Mapbox - For map integration.

    Hosted on Vercel.

Backend

    FastAPI - For handling API requests.

    MongoDB (Atlas) - As the database.

    WebSockets / MQTT (Optional) - For real-time communication.

    Hosted on Render.

Embedded System

    ESP32 - Microcontroller.

    GPS Module - For train location tracking.

    RFID Module - For train identification.

    MQTT (Planned) - For communication between ESP32 devices and the backend.

Deployment URLs
Frontend (Website Dashboard)

https://iot-project-xi.vercel.app/
Backend (FastAPI)

https://iot-project-c3wb.onrender.com/
How to Run Locally
Backend
cd fastapi-backend
pip install -r requirements.txt
uvicorn main:app --reload

The backend will run on http://127.0.0.1:8000.
Frontend
cd react-frontend
npm install
npm run dev

The frontend will run on http://localhost:5173/.
Future Plans

    Implement WebSockets for real-time updates.

    Integrate MQTT broker for ESP32 communication.

    Improve the user dashboard with live data visualization.

🚀 Built with FastAPI, React, and IoT technologies.


