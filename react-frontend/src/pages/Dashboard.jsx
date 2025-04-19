import React from 'react';
import TrainMap from '../components/TrainMap'; // ✅ import the map

const Dashboard = () => {
  return (
    <div>
      <h1 className="text-2xl font-bold mb-4">Dashboard</h1>

      {/* Add whatever else is on your dashboard */}

      <div className="mt-6">
        <h2 className="text-xl font-semibold mb-2">Live Train Map</h2>
        <TrainMap />
      </div>
    </div>
  );
};

export default Dashboard;