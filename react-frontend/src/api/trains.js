const BASE_URL = 'https://iot-project-c3wb.onrender.com/api';

export const fetchTrains = async (status) => {
  const query = status ? `?status=${status}` : '';
  const response = await fetch(`${BASE_URL}/trains/${query}`);
  if (!response.ok) {
    throw new Error('Failed to fetch trains');
  }
  return response.json();
};

export const createTrain = async (trainData) => {
  const response = await fetch(`${BASE_URL}/trains/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(trainData),
  });
  if (!response.ok) {
    throw new Error('Failed to create train');
  }
  return response.json();
};