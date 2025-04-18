import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    open: true, // Automatically opens the app in the browser
    port: 5173  // Custom port for development server
  }
});
