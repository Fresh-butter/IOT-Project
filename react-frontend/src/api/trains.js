const BASE_URL = 'https://iot-project-c3wb.onrender.com/api';

export const fetchTrains = async (params = {}) => {
  const query = new URLSearchParams(params).toString();
  const url = `${BASE_URL}/trains${query ? `?${query}` : ''}`;

  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Failed to fetch trains: ${response.status} ${response.statusText}`);
  }
  return response.json();
};