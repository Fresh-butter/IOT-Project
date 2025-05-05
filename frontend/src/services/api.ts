import axios from 'axios';

const BASE_URL = 'https://iot-project-c3wb.onrender.com/api';

// Define types for API responses
export interface Checkpoint {
  name?: string;
  interval: number;
  rfid_tag?: string;
  location: [number, number]; // [longitude, latitude]
}

export interface Route {
  _id: string;
  route_id: string;
  route_name: string;
  start_time?: string;
  assigned_train_id?: string;
  assigned_train_ref?: string;
  checkpoints: Checkpoint[];
}

// API function to fetch routes
export const fetchRoutes = async (): Promise<Route[]> => {
  try {
    const response = await axios.get(`${BASE_URL}/routes/`);
    return response.data;
  } catch (error) {
    console.error('Error fetching routes:', error);
    throw new Error('Failed to fetch routes. Please try again.');
  }
};