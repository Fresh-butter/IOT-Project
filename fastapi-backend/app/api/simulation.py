"""
Simulation API module.
Provides endpoints for testing the system without physical hardware.
"""
from fastapi import APIRouter, HTTPException, Body, Query, Path
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import random
import math

from app.models.train import TrainModel
from app.models.log import LogModel
from app.models.route import RouteModel
from app.services.train_service import TrainService
from app.config import get_current_ist_time, TRAIN_STATUS

router = APIRouter()

@router.post(
    "/generate-log", 
    summary="Generate simulated log entry", 
    description="Creates a simulated log entry for testing",
    response_model=Dict[str, Any]
)
async def generate_simulated_log(
    train_id: str = Query(..., description="Train identifier"),
    log_type: str = Query("location", description="Type of log to generate (location, rfid, status)"),
    error_probability: float = Query(0.0, ge=0.0, le=1.0, description="Probability of generating erroneous data")
):
    """
    Generate a simulated log entry for a train.
    """
    # Check if train exists
    train = await TrainModel.get_by_train_id(train_id)
    if not train:
        raise HTTPException(status_code=404, detail=f"Train {train_id} not found")
    
    # Get latest log to base new log on
    latest_log = await LogModel.get_latest_by_train(train_id)
    
    # Get current route
    route = None
    if train.get("current_route_id"):
        route = await RouteModel.get_by_route_id(train["current_route_id"])
    
    # Initialize log data
    log_data = {
        "timestamp": get_current_ist_time(),
        "event_type": "telemetry"
    }
    
    # Generate log data based on type
    if log_type == "location":
        # Generate location data
        if latest_log and latest_log.get("location"):
            # Base new location on previous location
            prev_location = latest_log["location"]
            
            # Add small random movement (~ 5-50 meters)
            movement_scale = 0.0005  # Approximately 50 meters
            
            # If we should introduce an error
            if random.random() < error_probability:
                # Create larger deviation
                movement_scale = 0.005  # Approximately 500 meters
            
            new_location = [
                prev_location[0] + random.uniform(-movement_scale, movement_scale),
                prev_location[1] + random.uniform(-movement_scale, movement_scale)
            ]
            
            # Round to 5 decimal places
            new_location = [round(coord, 5) for coord in new_location]
            
            log_data["location"] = new_location
            log_data["accuracy"] = random.choice(["excellent", "good", "moderate", "poor"])
            
            # Simulate GPS specifics
            log_data["details"] = {
                "speed_kmh": random.uniform(20, 60),
                "altitude": random.uniform(100, 500),
                "heading": random.uniform(0, 359)
            }
        else:
            # No previous location, generate a random one near Delhi
            delhi_coords = [77.2090, 28.6139]  # Delhi, India
            random_location = [
                delhi_coords[0] + random.uniform(-0.1, 0.1),
                delhi_coords[1] + random.uniform(-0.1, 0.1)
            ]
            
            # Round to 5 decimal places
            random_location = [round(coord, 5) for coord in random_location]
            
            log_data["location"] = random_location
            log_data["accuracy"] = random.choice(["excellent", "good", "moderate", "poor"])
            
            # Simulate GPS specifics
            log_data["details"] = {
                "speed_kmh": random.uniform(20, 60),
                "altitude": random.uniform(100, 500),
                "heading": random.uniform(0, 359)
            }
    
    elif log_type == "rfid":
        # Generate RFID tag detection
        if route and route.get("checkpoints"):
            # Get a random checkpoint with RFID tag
            rfid_checkpoints = [cp for cp in route["checkpoints"] if cp.get("rfid_tag")]
            
            if rfid_checkpoints:
                checkpoint = random.choice(rfid_checkpoints)
                log_data["rfid_tag"] = checkpoint["rfid_tag"]
                log_data["event_type"] = "rfid_detection"
                
                # If we have location for the checkpoint, use it
                if checkpoint.get("location"):
                    # Add small random error
                    error_margin = 0.00001  # ~1 meter
                    
                    # If we should introduce an error
                    if random.random() < error_probability:
                        error_margin = 0.0001  # ~10 meters
                    
                    location = [
                        checkpoint["location"][0] + random.uniform(-error_margin, error_margin),
                        checkpoint["location"][1] + random.uniform(-error_margin, error_margin)
                    ]
                    
                    # Round to 5 decimal places
                    location = [round(coord, 5) for coord in location]
                    
                    log_data["location"] = location
            else:
                # No RFID checkpoints, generate a random one
                log_data["rfid_tag"] = f"SIM{random.randint(10000, 99999)}"
                log_data["event_type"] = "rfid_detection"
        else:
            # No route, generate a random RFID tag
            log_data["rfid_tag"] = f"SIM{random.randint(10000, 99999)}"
            log_data["event_type"] = "rfid_detection"
    
    elif log_type == "status":
        # Generate status update
        current_status = train.get("current_status", TRAIN_STATUS["OUT_OF_SERVICE"])
        
        # List of possible statuses
        statuses = list(TRAIN_STATUS.values())
        
        # If we should introduce an error
        if random.random() < error_probability:
            # Pick a random status
            new_status = random.choice(statuses)
        else:
            # Pick a reasonable next status
            if current_status == TRAIN_STATUS["OUT_OF_SERVICE"]:
                new_status = TRAIN_STATUS["IN_SERVICE_NOT_RUNNING"]
            elif current_status == TRAIN_STATUS["IN_SERVICE_NOT_RUNNING"]:
                new_status = TRAIN_STATUS["IN_SERVICE_RUNNING"]
            elif current_status == TRAIN_STATUS["IN_SERVICE_RUNNING"]:
                new_status = TRAIN_STATUS["IN_SERVICE_NOT_RUNNING"]
            elif current_status == TRAIN_STATUS["MAINTENANCE"]:
                new_status = TRAIN_STATUS["IN_SERVICE_NOT_RUNNING"]
            else:
                new_status = TRAIN_STATUS["IN_SERVICE_NOT_RUNNING"]
        
        log_data["event_type"] = "status_change"
        log_data["details"] = {
            "old_status": current_status,
            "new_status": new_status
        }
    
    # Process the log with train service
    result = await TrainService.process_new_log(train_id, log_data)
    
    return {
        "success": True,
        "log_data": log_data,
        "processing_result": result
    }

@router.post(
    "/simulate-train-movement/{train_id}", 
    summary="Simulate train movement", 
    description="Simulates a train moving along its route",
    response_model=Dict[str, Any]
)
async def simulate_train_movement(
    train_id: str = Path(..., description="Train identifier"),
    duration_minutes: int = Query(10, ge=1, le=60, description="How long to simulate movement for"),
    interval_seconds: int = Query(60, ge=10, le=300, description="Interval between log entries"),
    with_errors: bool = Query(False, description="Whether to introduce errors in the simulation")
):
    """
    Simulate a train moving along its route.
    """
    # Check if train exists
    train = await TrainModel.get_by_train_id(train_id)
    if not train:
        raise HTTPException(status_code=404, detail=f"Train {train_id} not found")
    
    # Check if train has a route
    if not train.get("current_route_id"):
        raise HTTPException(status_code=400, detail=f"Train {train_id} doesn't have an assigned route")
    
    # Get the route
    route = await RouteModel.get_by_route_id(train["current_route_id"])
    if not route or not route.get("checkpoints") or len(route["checkpoints"]) < 2:
        raise HTTPException(status_code=400, detail="Route has insufficient checkpoints")
    
    # Calculate number of iterations
    iterations = (duration_minutes * 60) // interval_seconds
    
    # Get starting position
    latest_log = await LogModel.get_latest_by_train(train_id)
    
    start_location = None
    current_checkpoint_idx = 0
    
    if latest_log and latest_log.get("location"):
        start_location = latest_log["location"]
        
        # Find nearest checkpoint
        from app.core.location import find_nearest_checkpoint
        nearest_cp, cp_idx = await find_nearest_checkpoint(start_location, train["current_route_id"])
        
        if cp_idx != -1:
            current_checkpoint_idx = cp_idx
    else:
        # Start at the first checkpoint
        start_location = route["checkpoints"][0]["location"]
    
    # Prepare result tracking
    simulation_results = {
        "train_id": train_id,
        "route_id": train["current_route_id"],
        "duration_minutes": duration_minutes,
        "interval_seconds": interval_seconds,
        "iterations": iterations,
        "logs_created": [],
        "errors_introduced": 0,
        "start_time": get_current_ist_time()
    }
    
    # Simulate movement
    for i in range(iterations):
        # Determine target checkpoint
        target_idx = min(current_checkpoint_idx + 1, len(route["checkpoints"]) - 1)
        
        # If we reached the end of the route, stop simulation
        if current_checkpoint_idx >= len(route["checkpoints"]) - 1:
            break
        
        # Get current and target checkpoints
        current_cp = route["checkpoints"][current_checkpoint_idx]
        target_cp = route["checkpoints"][target_idx]
        
        # Calculate progress ratio based on iterations
        # This simplistic approach assumes constant speed
        progress_ratio = (i + 1) / iterations
        
        # Interpolate position between checkpoints
        interpolated_position = [
            current_cp["location"][0] + progress_ratio * (target_cp["location"][0] - current_cp["location"][0]),
            current_cp["location"][1] + progress_ratio * (target_cp["location"][1] - current_cp["location"][1])
        ]
        
        # Introduce error if requested
        error_introduced = False
        if with_errors and random.random() < 0.1:  # 10% chance of error
            # Add significant deviation
            error_margin = 0.001  # ~100 meters
            interpolated_position = [
                interpolated_position[0] + random.uniform(-error_margin, error_margin),
                interpolated_position[1] + random.uniform(-error_margin, error_margin)
            ]
            error_introduced = True
            simulation_results["errors_introduced"] += 1
        
        # Round to 5 decimal places
        interpolated_position = [round(coord, 5) for coord in interpolated_position]
        
        # Create the log
        log_data = {
            "timestamp": get_current_ist_time() + timedelta(seconds=i * interval_seconds),
            "location": interpolated_position,
            "accuracy": "poor" if error_introduced else "excellent",
            "event_type": "telemetry",
            "details": {
                "speed_kmh": random.uniform(30, 50),
                "heading": random.uniform(0, 359),
                "simulation": True
            }
        }
        
        # Check if we're close to an RFID checkpoint
        for cp_idx, checkpoint in enumerate(route["checkpoints"]):
            if checkpoint.get("rfid_tag") and checkpoint.get("location"):
                from app.utils import calculate_distance
                distance = calculate_distance(interpolated_position, checkpoint["location"])
                
                # If we're within 10 meters of an RFID checkpoint
                if distance < 10:
                    # Add RFID tag to the log
                    log_data["rfid_tag"] = checkpoint["rfid_tag"]
                    log_data["event_type"] = "rfid_detection"
                    
                    # Update current checkpoint
                    current_checkpoint_idx = cp_idx
                    break
        
        # Process the log
        result = await TrainService.process_new_log(train_id, log_data)
        
        # Track the result
        simulation_results["logs_created"].append({
            "location": log_data["location"],
            "timestamp": log_data["timestamp"],
            "has_rfid": "rfid_tag" in log_data,
            "log_id": result.get("log_id")
        })
    
    simulation_results["end_time"] = get_current_ist_time()
    
    return simulation_results

@router.post(
    "/simulate-collision/{train1_id}/{train2_id}", 
    summary="Simulate potential collision", 
    description="Simulates a potential collision scenario between two trains",
    response_model=Dict[str, Any]
)
async def simulate_collision(
    train1_id: str = Path(..., description="First train identifier"),
    train2_id: str = Path(..., description="Second train identifier"),
    collision_time_seconds: int = Query(300, ge=60, le=600, description="Time until simulated collision in seconds"),
    logs_per_train: int = Query(5, ge=3, le=10, description="Number of logs to generate per train")
):
    """
    Simulate a potential collision scenario between two trains.
    """
    # Check if trains exist
    train1 = await TrainModel.get_by_train_id(train1_id)
    train2 = await TrainModel.get_by_train_id(train2_id)
    
    if not train1:
        raise HTTPException(status_code=404, detail=f"Train {train1_id} not found")
    if not train2:
        raise HTTPException(status_code=404, detail=f"Train {train2_id} not found")
    
    # Get latest positions
    latest_log1 = await LogModel.get_latest_by_train(train1_id)
    latest_log2 = await LogModel.get_latest_by_train(train2_id)
    
    # Define starting positions
    start_pos1 = None
    start_pos2 = None
    
    if latest_log1 and latest_log1.get("location"):
        start_pos1 = latest_log1["location"]
    else:
        # Use a default position (Delhi)
        start_pos1 = [77.2090, 28.6139]
    
    if latest_log2 and latest_log2.get("location"):
        start_pos2 = latest_log2["location"]
    else:
        # Use a default position slightly offset from train1
        start_pos2 = [start_pos1[0] + 0.02, start_pos1[1] + 0.02]
    
    # Define a collision point as the midpoint between the two trains
    collision_point = [
        (start_pos1[0] + start_pos2[0]) / 2,
        (start_pos1[1] + start_pos2[1]) / 2
    ]
    
    # Calculate interval between logs
    interval_seconds = collision_time_seconds / logs_per_train
    
    # Track results
    simulation_results = {
        "train1_id": train1_id,
        "train2_id": train2_id,
        "collision_time_seconds": collision_time_seconds,
        "collision_point": collision_point,
        "logs_per_train": logs_per_train,
        "logs_created": [],
        "start_time": get_current_ist_time(),
        "alerts_generated": []
    }
    
    # Generate logs that gradually bring the trains closer
    for i in range(logs_per_train):
        # Calculate progress ratio
        progress_ratio = (i + 1) / logs_per_train
        
        # Calculate positions that converge toward collision point
        pos1 = [
            start_pos1[0] + progress_ratio * (collision_point[0] - start_pos1[0]),
            start_pos1[1] + progress_ratio * (collision_point[1] - start_pos1[1])
        ]
        
        pos2 = [
            start_pos2[0] + progress_ratio * (collision_point[0] - start_pos2[0]),
            start_pos2[1] + progress_ratio * (collision_point[1] - start_pos2[1])
        ]
        
        # Round to 5 decimal places
        pos1 = [round(coord, 5) for coord in pos1]
        pos2 = [round(coord, 5) for coord in pos2]
        
        # Calculate timestamp
        timestamp = get_current_ist_time() + timedelta(seconds=i * interval_seconds)
        
        # Create logs for both trains
        log1 = {
            "timestamp": timestamp,
            "location": pos1,
            "accuracy": "excellent",
            "event_type": "telemetry",
            "details": {
                "speed_kmh": random.uniform(30, 50),
                "heading": random.uniform(0, 359),
                "simulation": True
            }
        }
        
        log2 = {
            "timestamp": timestamp,
            "location": pos2,
            "accuracy": "excellent",
            "event_type": "telemetry",
            "details": {
                "speed_kmh": random.uniform(30, 50),
                "heading": random.uniform(0, 359),
                "simulation": True
            }
        }
        
        # Process the logs
        result1 = await TrainService.process_new_log(train1_id, log1)
        result2 = await TrainService.process_new_log(train2_id, log2)
        
        # Track the logs
        simulation_results["logs_created"].append({
            "train1_position": pos1,
            "train2_position": pos2,
            "timestamp": timestamp,
            "distance": round(
                math.sqrt((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2) * 111319.9,  # approx meters
                2
            )
        })
        
        # Check for collision risks and track alerts
        if "collision_risks" in result1 and result1["collision_risks"]:
            for risk in result1["collision_risks"]:
                if risk not in simulation_results["alerts_generated"]:
                    simulation_results["alerts_generated"].append(risk)
    
    simulation_results["end_time"] = get_current_ist_time()
    
    return simulation_results

@router.post(
    "/simulate-deviation/{train_id}", 
    summary="Simulate route deviation", 
    description="Simulates a train deviating from its assigned route",
    response_model=Dict[str, Any]
)
async def simulate_deviation(
    train_id: str = Path(..., description="Train identifier"),
    deviation_distance_meters: int = Query(200, ge=50, le=1000, description="Maximum deviation distance in meters"),
    logs_count: int = Query(5, ge=3, le=10, description="Number of logs to generate")
):
    """
    Simulate a train deviating from its assigned route.
    """
    # Check if train exists
    train = await TrainModel.get_by_train_id(train_id)
    if not train:
        raise HTTPException(status_code=404, detail=f"Train {train_id} not found")
    
    # Check if train has a route
    if not train.get("current_route_id"):
        raise HTTPException(status_code=400, detail=f"Train {train_id} doesn't have an assigned route")
    
    # Get the route
    route = await RouteModel.get_by_route_id(train["current_route_id"])
    if not route or not route.get("checkpoints") or len(route["checkpoints"]) < 2:
        raise HTTPException(status_code=400, detail="Route has insufficient checkpoints")
    
    # Get latest position
    latest_log = await LogModel.get_latest_by_train(train_id)
    
    start_location = None
    current_checkpoint_idx = 0
    
    if latest_log and latest_log.get("location"):
        start_location = latest_log["location"]
        
        # Find nearest checkpoint
        from app.core.location import find_nearest_checkpoint
        nearest_cp, cp_idx = await find_nearest_checkpoint(start_location, train["current_route_id"])
        
        if cp_idx != -1:
            current_checkpoint_idx = cp_idx
    else:
        # Start at the first checkpoint
        start_location = route["checkpoints"][0]["location"]
    
    # If we're at the last checkpoint, move back one
    if current_checkpoint_idx >= len(route["checkpoints"]) - 1:
        current_checkpoint_idx = len(route["checkpoints"]) - 2
    
    # Get current and next checkpoint
    current_cp = route["checkpoints"][current_checkpoint_idx]
    next_cp = route["checkpoints"][current_checkpoint_idx + 1]
    
    # Calculate route direction vector
    route_direction = [
        next_cp["location"][0] - current_cp["location"][0],
        next_cp["location"][1] - current_cp["location"][1]
    ]
    
    # Normalize the direction vector
    direction_length = math.sqrt(route_direction[0]**2 + route_direction[1]**2)
    if direction_length > 0:
        route_direction = [
            route_direction[0] / direction_length,
            route_direction[1] / direction_length
        ]
    
    # Calculate perpendicular vector (rotate 90 degrees)
    perpendicular = [route_direction[1], -route_direction[0]]
    
    # Track results
    simulation_results = {
        "train_id": train_id,
        "route_id": train["current_route_id"],
        "deviation_distance_meters": deviation_distance_meters,
        "logs_count": logs_count,
        "logs_created": [],
        "start_time": get_current_ist_time(),
        "alerts_generated": []
    }
    
    # Convert deviation distance to degrees (approximate)
    # 1 degree latitude ≈ 111 km at the equator
    degree_conversion = 111000  # meters per degree (approximate)
    max_deviation_degrees = deviation_distance_meters / degree_conversion
    
    # Generate logs with increasing deviation
    for i in range(logs_count):
        # Calculate progress along route (0.1 to 0.9)
        route_progress = 0.1 + (0.8 * i / (logs_count - 1)) if logs_count > 1 else 0.5
        
        # Calculate deviation amount (increases then decreases)
        deviation_factor = math.sin(route_progress * math.pi) * max_deviation_degrees
        
        # Calculate position with progress along route and deviation perpendicular to route
        position = [
            current_cp["location"][0] + route_progress * (next_cp["location"][0] - current_cp["location"][0]) + perpendicular[0] * deviation_factor,
            current_cp["location"][1] + route_progress * (next_cp["location"][1] - current_cp["location"][1]) + perpendicular[1] * deviation_factor
        ]
        
        # Round to 5 decimal places
        position = [round(coord, 5) for coord in position]
        
        # Calculate timestamp
        timestamp = get_current_ist_time() + timedelta(seconds=i * 60)  # One minute between logs
        
        # Create log
        log_data = {
            "timestamp": timestamp,
            "location": position,
            "accuracy": "excellent",
            "event_type": "telemetry",
            "details": {
                "speed_kmh": random.uniform(30, 50),
                "heading": random.uniform(0, 359),
                "simulation": True
            }
        }
        
        # Process the log
        result = await TrainService.process_new_log(train_id, log_data)
        
        # Calculate actual deviation distance
        from app.utils import calculate_distance
        from app.core.tracking import min_distance_point_to_line
        
        actual_deviation = min_distance_point_to_line(
            position, 
            current_cp["location"], 
            next_cp["location"]
        )
        
        # Track the log
        simulation_results["logs_created"].append({
            "position": position,
            "timestamp": timestamp,
            "deviation_meters": round(actual_deviation, 2),
            "log_id": result.get("log_id")
        })
        
        # Check for deviation alerts
        from app.core.tracking import detect_route_deviations
        deviation_result = await detect_route_deviations(train_id)
        if deviation_result.get("deviation_detected"):
            if deviation_result not in simulation_results["alerts_generated"]:
                simulation_results["alerts_generated"].append(deviation_result)
    
    simulation_results["end_time"] = get_current_ist_time()
    
    return simulation_results