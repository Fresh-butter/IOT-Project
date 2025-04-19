import React from 'react';
import { Link } from 'react-router-dom';

const Navbar = () => {
  return (
    <nav className="bg-blue-600 text-white p-4">
      <h1 className="text-lg font-bold">Train Collision Avoidance System</h1>
      <div className="flex space-x-4">
        <Link to="/" className="hover:underline">Dashboard</Link>
        <Link to="/trains" className="hover:underline">Trains</Link>
        <Link to="/routes" className="hover:underline">Routes</Link>
        <Link to="/alerts" className="hover:underline">Alerts</Link>
        <Link to="/logs" className="hover:underline">Logs</Link>
        <Link to="/analytics" className="hover:underline">Analytics</Link>
        <Link to="/api-docs" className="hover:underline">API Docs</Link>
      </div>
    </nav>
  );
};

export default Navbar;