# MongoDB Schema Documentation

## users

```json
{
  "username": "Navneet",
  "hashed_password": "*****"
}
```
## trains

```json
{
  "train_id": 101,
  "name": "IIITH Express",
  "current_status": "in_service_running",
  "current_route_id": "R101",
  "current_route_ref": { "$oid": "67e80645e4a58df990138c2b" }
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
  "assigned_train_ref": {
    "$oid": "67e80645e4a58df990138c2b"
  },
  "checkpoints": [
    {
      "interval": 0,
      "rfid_tag": "RFID_101_A1",
      "location": [77.209, 28.6139]
    },
    {
      "interval": 3600,
      "rfid_tag": null,
      "location": [77.1025, 28.7041]
    },
    {
      "interval": 7200,
      "rfid_tag": "RFID_101_B2",
      "location": [76.8512, 28.7041]
    }
  ]
}
```

*interval is in seconds