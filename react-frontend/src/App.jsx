import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Navbar from './components/Navbar';
import Footer from './components/Footer';
import Dashboard from './pages/Dashboard';
import ApiDocs from './pages/ApiDocs';
import Trains from './pages/Trains';
import RoutesPage from './pages/Routes'; // Import the Routes page

const App = () => {
  return (
    <Router>
      <Navbar />
      <div className="container mx-auto p-4">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/trains" element={<Trains />} />
          <Route path="/routes" element={<RoutesPage />} /> {/* Add this route */}
          <Route path="/api-docs" element={<ApiDocs />} />
        </Routes>
      </div>
      <Footer />
    </Router>
  );
};

export default App;