const BASE_URL = 'https://iot-project-c3wb.onrender.com/api';

export const fetchRoutes = async () => {
  const response = await fetch(`${BASE_URL}/routes/`);
  if (!response.ok) {
    throw new Error('Failed to fetch routes');
  }
  return response.json();
};