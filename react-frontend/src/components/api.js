import axios from 'axios';

const API_BASE_URL = 'https://iot-project-c3wb.onrender.com';

export const getLiveData = async () => {
  const response = await axios.get(`${API_BASE_URL}/live-data`);
  return response.data;
};
