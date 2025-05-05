# GPS & RFID-Based Train Location Monitoring & Collision Avoidance System

## Repository Structure

### Root Folder
- **`README.md`**: README file for the project, containing Repository structure, setup instructions, deployment URLs, and future plans.
- **`schema.md`**: Contains the database schema or data structure used in the project, detailing collections, fields, and relationships in MongoDB.
- **`Project-proposal.docx`**: The project proposal conataining motivation, scope, and deliverabales.
- **`IoT-Project-Report.docx`**: The final project report, providing a comprehensive explanation of the project, including technical details, challenges, and conclusions.

### `fastapi-backend/`
- **`main.py`**: The entry point for the FastAPI application.
- **`requirements.txt`**: Lists all Python dependencies required for the backend.
- Other backend-related files for API development and database integration.

### `react-frontend/`
- **`src/`**: The source folder for React components and logic.
  - **`App.tsx`**: The main React component that initializes the app.
  - **`components/`**: Contains reusable React components like `Header` and `RoutesList`.
- **`public/`**: Contains static assets like images or icons.
- **`package.json`**: Defines Node.js dependencies and scripts for the frontend.
- **`vite.config.ts`**: Configuration file for Vite.

### `hardware-configuration-and-code/`
- **`V0_GPS.md`**: Documentation and code for the initial GPS module setup.
- **`V0_RFID.md`**: Documentation and code for the initial RFID reader setup.
- **`V1_Intermediate.md`**: Intermediate embedded system code and configuration for the ESP32 microcontroller, integrating GPS module and RFID reader.
- **`V2_Final.md`**: Final embedded system code and configuration for the ESP32 microcontroller, integrating GPS module and RFID reader.


### `data-collection/`
- **`overview.md`**: Provides an overview of the trial runs conducted.
- **`trial_{i}.md`**: Contains the data of the ith trial.

### `react-frontend-deappreciated/`
- deappreciated frontend implementation



## Technologies Used

### Frontend
- **React.js (with Vite)** - For building the web dashboard.
- **Leaflet.js** - For map integration.
- **Hosted on Vercel**.

### Backend
- **FastAPI** - For handling API requests.
- **MongoDB (Atlas)** - As the database.
- **Hosted on Render**.

### Embedded System
- **ESP32** - Microcontroller.
- **GPS Module** - For train location tracking.
- **RFID Module** - For train identification.

## Deployment URLs

### Frontend (Website Dashboard)
🔗 [Live Site](https://iot-project-xi.vercel.app/)

### Backend (FastAPI)
🔗 [API Server](https://iot-project-c3wb.onrender.com/)

## How to Run Locally

### Backend
```sh
cd fastapi-backend
pip install -r requirements.txt
uvicorn main:app --reload
```
🔹 The backend will run on **[http://127.0.0.1:8000](http://127.0.0.1:8000)**.

### Frontend
```sh
cd react-frontend
npm install
npm run dev
```
🔹 The frontend will run on **[http://localhost:5173](http://localhost:5173)**.

## Future Plans
- ✅ Improve the **user dashboard** with live data visualization.

