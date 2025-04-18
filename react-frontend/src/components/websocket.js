export const connectWebSocket = () => {
  const socket = new WebSocket('wss://iot-project-c3wb.onrender.com/ws');
  socket.onopen = () => console.log('WebSocket connected');
  socket.onmessage = (event) => console.log('Message received:', event.data);
  socket.onclose = () => console.log('WebSocket disconnected');
  return socket;
};
