const BASE_URL = 'https://iot-project-c3wb.onrender.com/api';

export const fetchAlerts = async () => {
  const response = await fetch(`${BASE_URL}/alerts/alerts/`);
  if (!response.ok) {
    throw new Error('Failed to fetch alerts');
  }
  return response.json();
};