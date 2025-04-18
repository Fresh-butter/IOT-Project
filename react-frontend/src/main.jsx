import 'leaflet/dist/leaflet.css';
import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './main.css'; // Import Tailwind CSS or your global CSS file

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
