import React, { useEffect, useState } from 'react';
import { fetchTrains } from '../api/trains';

const Trains = () => {
  const [trains, setTrains] = useState([]);
  const [error, setError] = useState(null);

  useEffect(() => {
    const loadTrains = async () => {
      try {
        const data = await fetchTrains();
        setTrains(data);
      } catch (err) {
        setError(err.message);
      }
    };
    loadTrains();
  }, []);

  return (
    <div className="p-4">
      <h2 className="text-2xl font-bold mb-4">Trains</h2>
      {error && <p className="text-red-500">{error}</p>}
      <ul>
        {trains.map((train) => (
          <li key={train.train_id}>
            {train.name} - Status: {train.current_status}
          </li>
        ))}
      </ul>
    </div>
  );
};

export default Trains;