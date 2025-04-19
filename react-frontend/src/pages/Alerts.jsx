import React, { useEffect, useState } from 'react';
import { fetchAlerts } from '../api/alerts';

const AlertsPage = () => {
  const [alerts, setAlerts] = useState([]);
  const [error, setError] = useState(null);

  useEffect(() => {
    const loadAlerts = async () => {
      try {
        const data = await fetchAlerts();
        setAlerts(data);
      } catch (err) {
        setError(err.message);
      }
    };
    loadAlerts();
  }, []);

  return (
    <div className="p-4">
      <h2 className="text-2xl font-bold mb-4">Collision Alerts</h2>
      {error && <p className="text-red-500">{error}</p>}
      <ul>
        {alerts.map((alert, index) => (
          <li key={index}>
            {alert.message} - {alert.timestamp}
          </li>
        ))}
      </ul>
    </div>
  );
};

export default AlertsPage;