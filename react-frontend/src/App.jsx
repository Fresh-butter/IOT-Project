import 'leaflet/dist/leaflet.css';
import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Navbar from './components/Navbar';
import Footer from './components/Footer';
import Dashboard from './pages/Dashboard';
import Trains from './pages/Trains';
import RoutesPage from './pages/Routes';
import AlertsPage from './pages/Alerts'; // Import AlertsPage

const App = () => {
  return (
    <Router>
      <Navbar />
      <div className="container mx-auto p-4">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/trains" element={<Trains />} />
          <Route path="/routes" element={<RoutesPage />} />
          <Route path="/alerts" element={<AlertsPage />} /> {/* Add Alerts Route */}
        </Routes>
      </div>
      <Footer />
    </Router>
  );
};

export default App;