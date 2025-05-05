import React, { useEffect, useState } from 'react';
import { fetchAlerts } from '../api/alerts';

const AlertsPage = () => {
  const [alerts, setAlerts] = useState([]);
  const [error, setError] = useState(null);
  const [isUpdated, setIsUpdated] = useState(false);

  useEffect(() => {
    const loadAlerts = async () => {
      try {
        const data = await fetchAlerts();
        if (JSON.stringify(data) !== JSON.stringify(alerts)) {
          setAlerts(data);
          setIsUpdated(true); // Set flag to true when new alerts are fetched
        } else {
          setIsUpdated(false); // No updates
        }
      } catch (err) {
        setError(err.message);
      }
    };

    // Initial load
    loadAlerts();

    // Poll every 10 seconds for updates
    const interval = setInterval(loadAlerts, 10000);
    return () => clearInterval(interval); // Cleanup on component unmount
  }, [alerts]);

  return (
    <div className="p-4">
      <h2 className="text-2xl font-bold mb-4">Collision Alerts</h2>
      {error && <p className="text-red-500">{error}</p>}
      <p className={`mb-4 ${isUpdated ? 'text-green-500' : 'text-gray-500'}`}>
        {isUpdated ? 'Updated' : 'Not Updated'}
      </p>
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