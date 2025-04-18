import React, { useEffect, useState } from 'react';
import { getLiveData } from '../services/api';

const LiveData = () => {
  const [data, setData] = useState([]);

  useEffect(() => {
    const fetchData = async () => {
      const liveData = await getLiveData();
      setData(liveData);
    };
    fetchData();
  }, []);

  return (
    <div className="p-4 bg-white rounded shadow">
      <h3 className="text-xl font-bold mb-2">Live Train Data</h3>
      <ul>
        {data.map((item, index) => (
          <li key={index}>{item.name}: {item.status}</li>
        ))}
      </ul>
    </div>
  );
};

export default LiveData;
