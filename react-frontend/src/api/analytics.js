import { useState, useEffect } from "react";
import { fetchAlerts } from "../api/alerts"; // Fetch alerts from backend

// Utility function to categorize alerts
const categorizeAlerts = (alerts) => {
  const alertCounts = {};
  alerts.forEach((alert) => {
    const { message } = alert;
    const category = message.toLowerCase().includes("collision")
      ? "Collision"
      : message.toLowerCase().includes("deviation")
      ? "Deviation"
      : message.toLowerCase().includes("schedule")
      ? "Schedule"
      : "Other";

    alertCounts[category] = (alertCounts[category] || 0) + 1;
  });
  return alertCounts;
};

const Analytics = () => {
  const [analytics, setAnalytics] = useState({});
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchAndCategorizeAlerts = async () => {
      try {
        const alerts = await fetchAlerts(); // Fetch alerts from backend
        const categorizedData = categorizeAlerts(alerts); // Categorize alerts
        setAnalytics(categorizedData); // Store analytics
      } catch (err) {
        setError(err.message);
      }
    };

    fetchAndCategorizeAlerts();

    // Optionally, poll for updates every 10 seconds
    const interval = setInterval(fetchAndCategorizeAlerts, 10000);
    return () => clearInterval(interval); // Cleanup on component unmount
  }, []);

  return (
    <div>
      <h2>Alert Analytics</h2>
      {error && <p className="error">{error}</p>}
      <ul>
        {Object.entries(analytics).map(([category, count]) => (
          <li key={category}>
            {category}: {count}
          </li>
        ))}
      </ul>
    </div>
  );
};

export default Analytics;