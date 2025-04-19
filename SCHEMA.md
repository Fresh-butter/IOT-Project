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

### Train Status Reference

| Status                  | Description                                             |
|-------------------------|---------------------------------------------------------|
| `in_service_running`     | Train is currently running on its assigned route.                      |
| `in_service_not_running` | Route assigned but train is currently halted (station/emergency)       |
| `maintenance`            | Route assigned but train not running (default)                         |
| `out_of_service`         | No assigned route; route_id and route_ref are null                     |


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
      "name": null,
      "interval": 0,
      "rfid_tag": "RFID_101_A1",
      "location": [77.20900, 28.61390]
    },
    {
      "name": "station_alpha",
      "interval": 3600,
      "rfid_tag": null,
      "location": [77.10250, 28.70410]
    },
    {
      "name": null,
      "interval": 7200,
      "rfid_tag": "RFID_101_B2",
      "location": [76.85125, 28.70412]
    }
  ]
}
```
### Notes
- `assigned_train_id` and `assigned_train_ref` can be null if no train has been assigned
- `start_time` can be `null`. In that case, the actual start time is whenever the train starts running on the route.
- `checkpoints` is an array of locations the train is expected to reach.
- `interval` (in **seconds**) represents expected time to pass the checkpoint from start time
  
- `rfid_tag` can be `null` if no RFID scan is expected at that checkpoint.
- `name`, if **null**, the checkpoint is not a station. If a string, the checkpoint is a station with a human-readable name.


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
### Notes
- `rfid_tag` can be `null` if no RFID tag was detected during this log entry.
- `location` can be `null` if no valid GPS signal was available during this log entry.
- `accuracy` indicates the GPS signal quality based on HDOP and satellite count (see table below).
- `is_test` is set to `true` if the data is for testing purposes only. When `true`, the backend will record the data but not run collision detection or other functionality on it.

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
  "sender_ref": "67e80281e4a58df990138c24",
  "recipient_ref": "67e802cee4a58df990138c26",
  "message": "Train 202 stopped unexpectedly.",
  "location": [76.85125, 28.70412],   
  "timestamp": "2025-04-10T14:23:05+05:30"
}
```

### Alert System Notes
- System-generated alerts use a default sender_ref: "680142a4f8db812a8b87617c"
- Every alert by system is sent to both the intended recipient train and to a "guest" account with recipient_ref: "680142cff8db812a8b87617d"

### Standard System Alert Messages

The system generates the following standard alert types:

#### Collision Alerts
- `COLLISION_WARNING: Potential collision risk between Train {train_id1} and Train {train_id2}`
- `COLLISION_RESOLVED: Collision risk between Train {train_id1} and Train {train_id2} resolved`

#### Route Deviation Alerts
- `DEVIATION_WARNING: Train {train_id} deviated from route {route_id} by {distance}m`
- `DEVIATION_RESOLVED: Train {train_id} returned to route {route_id}`

#### System Status Alerts
- `TRAIN_STOPPED: Train {train_id} stopped at {location}`
- `TRAIN_RESUMED: Train {train_id} resumed operation`
- `SYSTEM_WARNING: {custom_message}`