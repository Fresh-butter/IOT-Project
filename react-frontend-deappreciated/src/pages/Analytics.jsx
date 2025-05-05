import React, { useState, useEffect } from "react";

// Utility function to format API response
const formatAnalyticsData = (data) => ({
  totalAlerts: data.total_alerts || 0,
  activeTrains: data.train_count?.active || 0,
  outOfServiceTrains: data.train_count?.out_of_service || 0,
  totalTrains: data.train_count?.total || 0,
  logCount: data.log_count || 0,
});

const Analytics = () => {
  const [analytics, setAnalytics] = useState({});
  const [error, setError] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);

  useEffect(() => {
    // Function to fetch analytics from the backend
    const fetchAnalytics = async () => {
      try {
        const response = await fetch(
          "https://iot-project-c3wb.onrender.com/api/analytics/system-status?hours=24",
          {
            headers: {
              accept: "application/json",
            },
          }
        );

        if (!response.ok) {
          throw new Error(`Failed to fetch analytics: ${response.statusText}`);
        }

        const data = await response.json();
        setAnalytics(formatAnalyticsData(data));
        setLastUpdated(new Date()); // Update the last updated timestamp
        setError(null); // Clear any previous error
      } catch (err) {
        setError(err.message);
      }
    };

    // Initial fetch
    fetchAnalytics();

    // Poll for analytics data every 10 seconds
    const interval = setInterval(fetchAnalytics, 10000);

    // Cleanup interval on component unmount
    return () => clearInterval(interval);
  }, []);

  // Check if the data is updated
  const isUpdated = lastUpdated
    ? (new Date() - lastUpdated) / 1000 <= 10 // Check if the last update was within the last 10 seconds
    : false;

  return (
    <div>
      <h2>System Analytics</h2>
      {error && <p className="error">{error}</p>}
      <p>
        Updated: <strong>{isUpdated ? "Yes, it is updated" : "No, it is not updated"}</strong>
      </p>
      <ul>
        <li>Total Alerts: {analytics.totalAlerts}</li>
        <li>Total Trains: {analytics.totalTrains}</li>  
        <li>Active Trains: {analytics.activeTrains}</li>
        <li>Out-of-Service Trains: {analytics.outOfServiceTrains}</li>
        <li>Log Count: {analytics.logCount}</li>
      </ul>
      <p>
        Last Updated:{" "}
        {lastUpdated ? lastUpdated.toLocaleTimeString() : "Never"}
      </p>
    </div>
  );
};

export default Analytics;