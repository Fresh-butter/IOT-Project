import React from 'react';

const ApiDocs = () => {
  return (
    <div className="p-4">
      <h2 className="text-2xl font-bold mb-4">API Documentation</h2>
      <iframe
        src="https://iot-project-c3wb.onrender.com"
        title="Swagger UI"
        width="100%"
        height="600px"
        style={{ border: 'none' }}
      ></iframe>
    </div>
  );
};

export default ApiDocs;