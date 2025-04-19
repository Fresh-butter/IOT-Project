import axios from 'axios';

const API_BASE_URL = 'https://iot-project-c3wb.onrender.com';

// Example function to fetch live data
export const getLiveData = async () => {
  try {
    const response = await axios.get(`${API_BASE_URL}/api/routes/`);
    return response.data;
  } catch (error) {
    console.error('Error fetching live data:', error);
    throw error;
  }
};
