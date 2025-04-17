def classify_gps_accuracy(hdop: float | None, satellites: int | None) -> dict:
    if hdop is None or satellites is None or satellites == 0:
        return {
            "category": "Invalid",
            "description": "No GPS fix",
            "error_m": None
        }

    if hdop <= 1.0 and satellites >= 6:
        return {
            "category": "Excellent",
            "description": "< 5 meter error",
            "error_m": "<5"
        }
    elif 1.0 < hdop <= 2.0 and satellites >= 5:
        return {
            "category": "Good",
            "description": "5–10 meter error",
            "error_m": "5–10"
        }
    elif 2.0 < hdop <= 5.0 and satellites >= 4:
        return {
            "category": "Moderate",
            "description": "10–25 meter error",
            "error_m": "10–25"
        }
    elif 5.0 < hdop <= 10.0 and satellites >= 3:
        return {
            "category": "Poor",
            "description": "25–50 meter error",
            "error_m": "25–50"
        }
    else:
        return {
            "category": "Very Poor or Invalid",
            "description": "> 50 meter error or no fix",
            "error_m": ">50"
        }
