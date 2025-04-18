import React from 'react';
import Map from './Map';
import LiveData from './LiveData';

const Dashboard = () => {
  return (
    <div className="p-4">
      <h2 className="text-2xl font-bold mb-4">Dashboard</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Map />
        <LiveData />
      </div>
    </div>
  );
};

export default Dashboard;
