# MongoDB Schema Documentation

## trains

```json
{
  "train_id": "101",
  "name": "IIITH Express",
  "current_status": "in_service_running",
  "current_route_id": "R101",
  "current_route_ref": "67e80645e4a58df990138c2b"
}
```

*allowed_statuses = [ "in_service_running", "in_service_not_running", "maintenance", "out_of_service" ]

## routes

```json
{
  "route_id": "R101",
  "route_name": "Delhi to Mumbai",
  "start_time": "2025-03-29T19:30:00+05:30",
  "assigned_train_id": "101",
  "assigned_train_ref": "67e80645e4a58df990138c2b",
  "checkpoints": [
    {
      "interval": 0,
      "rfid_tag": "RFID_101_A1",
      "location": [77.20900, 28.61390]
    },
    {
      "interval": 3600,
      "rfid_tag": null,
      "location": [77.10250, 28.70410]
    },
    {
      "interval": 7200,
      "rfid_tag": "RFID_101_B2",
      "location": [76.85125, 28.70412]
    }
  ]
}
```

*interval is in seconds

## logs

```json
{
  "train_id": "101",
  "train_ref": "67e80645e4a58df990138c2b",
  "rfid_tag": "RFID_101_B2",               
  "location": [76.85125, 28.70412],          
  "timestamp": "2025-04-10T14:23:05+05:30",
  "accuracy": "good",                      
  "is_test": false                        
}
```
### GPS Accuracy Classification (Based on HDOP and Satellite Count)

| HDOP Range      | Minimum Satellites | Category           | Description             | Estimated Error (m) |
|-----------------|--------------------|--------------------|-------------------------|----------------------|
| ≤ 1.0           | ≥ 6                | Excellent          | Ideal GPS fix           | < 5                  |
| 1.0 – 2.0       | ≥ 5                | Good               | Strong and accurate fix | 5 – 10               |
| 2.0 – 5.0       | ≥ 4                | Moderate           | Acceptable, some errors | 10 – 25              |
| 5.0 – 10.0      | ≥ 3                | Poor               | Weak GPS fix            | 25 – 50              |
| > 10.0 or N/A   | < 3 or None        | Very Poor/Invalid  | Very high error or no fix | > 50 or No Fix     |

## alerts

```json
{
  "sender_id": "67e80281e4a58df990138c24",
  "recipient_id": "67e802cee4a58df990138c26",
  "message": "Train 202 stopped unexpectedly.",
  "location": [76.85125, 28.70412],   
  "timestamp": "2025-04-10T14:23:05+05:30"
}
```