import React, { useEffect, useState } from 'react';
import { fetchTrains } from '../api/trains';

const Trains = () => {
  const [trains, setTrains] = useState([]);
  const [error, setError] = useState(null);
  const [status, setStatus] = useState(''); // State for selected status

  // Function to load trains based on status
  const loadTrains = async (selectedStatus) => {
    try {
      const data = await fetchTrains({ status: selectedStatus });
      setTrains(data);
      setError(null); // Reset error state on successful fetch
    } catch (err) {
      setError(err.message);
      setTrains([]); // Clear trains if there's an error
    }
  };

  // Handle form submission
  const handleSubmit = (e) => {
    e.preventDefault();
    loadTrains(status); // Fetch trains with selected status
  };

  return (
    <div className="p-4">
      <h2 className="text-2xl font-bold mb-4">Trains</h2>

      {/* Error Message */}
      {error && <p className="text-red-500">{error}</p>}

      {/* Filtering Form */}
      <form onSubmit={handleSubmit} className="mb-4">
        <label className="block text-gray-700 mb-2">Select Train Status:</label>
        <select
          className="border p-2 w-full mb-4"
          value={status}
          onChange={(e) => setStatus(e.target.value)}
          required
        >
          <option value="">-- Select Status --</option>
          <option value="in_service_running">In Service Running</option>
          <option value="in_service_not_running">In Service Not Running</option>
          <option value="maintenance">Maintenance</option>
          <option value="out_of_service">Out of Service</option>
        </select>
        <button
          type="submit"
          className="bg-blue-500 text-white px-4 py-2 rounded"
        >
          Filter Trains
        </button>
      </form>

      {/* Display Filtered Trains */}
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