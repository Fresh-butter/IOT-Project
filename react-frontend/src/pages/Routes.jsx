import React, { useEffect, useState } from 'react';
import { fetchRoutes } from '../api/routes';

const RoutesPage = () => {
  const [routes, setRoutes] = useState([]);
  const [error, setError] = useState(null);

  useEffect(() => {
    const loadRoutes = async () => {
      try {
        const data = await fetchRoutes();
        setRoutes(data);
      } catch (err) {
        setError(err.message);
      }
    };
    loadRoutes();
  }, []);

  return (
    <div className="p-4">
      <h2 className="text-2xl font-bold mb-4">Routes</h2>
      {error && <p className="text-red-500">{error}</p>}
      <ul>
        {routes.map((route) => (
          <li key={route.route_id}>
            {route.route_name} - Start Time: {route.start_time}
          </li>
        ))}
      </ul>
    </div>
  );
};

export default RoutesPage;