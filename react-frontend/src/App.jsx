import { useEffect, useState } from "react";
import axios from "axios";

function App() {
    const [message, setMessage] = useState("");

    useEffect(() => {
        axios.get("https://iot-project-c3wb.onrender.com/")
            .then(response => setMessage(response.data.message))
            .catch(error => console.error(error));
    }, []);

    return (
        <div>
            <h1>Train Collision System</h1>
            <p>Backend says: {message}</p>
        </div>
    );
}

export default App;
