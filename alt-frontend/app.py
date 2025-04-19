from flask import Flask, render_template
import random

app = Flask(__name__)

# Mock data for trains
trains = [
    {"name": "Train A", "latitude": 12.9716, "longitude": 77.5946, "speed": 80, "alert": 0},
    {"name": "Train B", "latitude": 12.2958, "longitude": 76.6394, "speed": 100, "alert": 1},
]

@app.route('/')
def index():
    return render_template("index.html", trains=trains)

if __name__ == "__main__":
    app.run(debug=True)
