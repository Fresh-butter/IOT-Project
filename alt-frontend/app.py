from flask import Flask, render_template
import requests

app = Flask(__name__)

# Backend API base URL
API_BASE_URL = "https://iot-project-c3wb.onrender.com"  # Ensure no trailing slash

@app.route('/')
def index():
    try:
        # Fetch data from the backend
        trains = requests.get(f"{API_BASE_URL}/trains").json()
        alerts = requests.get(f"{API_BASE_URL}/alerts").json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        trains = []
        alerts = []
    return render_template("index.html", trains=trains, alerts=alerts)

if __name__ == "__main__":
    app.run(debug=True)  # Use debug=True only in development
