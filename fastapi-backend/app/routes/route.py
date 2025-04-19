"""
Route routes module.
Defines API endpoints for route operations.
"""
from fastapi import APIRouter, HTTPException, status, Body, Path, Query, Depends
from typing import List, Optional, Dict, Any
from app.models.route import RouteModel
from app.models.train import TrainModel
from app.schemas.route import RouteCreate, RouteUpdate, RouteInDB
from app.utils import handle_exceptions, normalize_timestamp
from app.database import safe_db_operation
from app.config import get_current_utc_time

router = APIRouter()

@router.post("/", 
             response_model=RouteInDB, 
             status_code=status.HTTP_201_CREATED,
             summary="Create a new route",
             description="Create a new route with the provided information")
@handle_exceptions("creating route")
async def create_route(route: RouteCreate = Body(...)):
    """Create a new route"""
    route_dict = route.dict()
    
    # Ensure start_time is normalized to UTC for storage
    if "start_time" in route_dict and route_dict["start_time"]:
        route_dict["start_time"] = normalize_timestamp(route_dict["start_time"])
    
    route_id = await RouteModel.create(route_dict)
    created_route = await RouteModel.get_by_id(route_id)
    if not created_route:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                          detail="Failed to retrieve created route")
    return RouteInDB(**created_route)

@router.get("/", 
           response_model=List[RouteInDB],
           summary="Get all routes",
           description="Retrieve a list of all routes")
@handle_exceptions("retrieving routes")
async def get_routes():
    """Get all routes"""
    routes = await RouteModel.get_all()
    return [RouteInDB(**route) for route in routes]

@router.get("/{id}", 
           response_model=RouteInDB,
           summary="Get route by ID",
           description="Retrieve a specific route by its ID")
@handle_exceptions("retrieving route")
async def get_route(id: str = Path(..., description="The ID of the route to retrieve")):
    """Get a route by ID"""
    route = await RouteModel.get_by_id(id)
    if not route:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Route not found")
    return RouteInDB(**route)

@router.put("/{id}", 
            response_model=RouteInDB,
            summary="Update an existing route",
            description="Update the details of an existing route by its ID")
@handle_exceptions("updating route")
async def update_route(
    id: str = Path(..., description="The ID of the route to update"),
    route: RouteUpdate = Body(...)
):
    """Update an existing route"""
    update_data = route.dict(exclude_unset=True)
    
    # Nothing to update
    if not update_data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, 
                          detail="No valid update data provided")
    
    # Ensure start_time is normalized to UTC for storage if it's being updated
    if "start_time" in update_data and update_data["start_time"]:
        update_data["start_time"] = normalize_timestamp(update_data["start_time"])
    
    # Update the route
    updated = await RouteModel.update(id, update_data)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Route not found")
    
    # Return the updated route
    updated_route = await RouteModel.get_by_id(id)
    return RouteInDB(**updated_route)

@router.delete("/{id}", 
              response_model=Dict[str, str],
              summary="Delete a route",
              description="Delete a route by its ID")
@handle_exceptions("deleting route")
async def delete_route(id: str = Path(..., description="The ID of the route to delete")):
    """Delete a route by ID"""
    deleted = await RouteModel.delete(id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Route not found")
    
    return {"message": "Route deleted successfully"}

@router.post("/{route_id}/assign-train/{train_id}", 
            response_model=Dict[str, str],
            summary="Assign a train to a route",
            description="Assign an existing train to an existing route")
@handle_exceptions("assigning train to route")
async def assign_train_to_route(
    route_id: str = Path(..., description="The route_id of the route"),
    train_id: str = Path(..., description="The train_id of the train")
):
    """Assign a train to a route"""
    # Check if the route exists
    route = await RouteModel.get_by_route_id(route_id)
    if not route:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                          detail=f"Route with ID {route_id} not found")
    
    # Check if the train exists
    train = await TrainModel.get_by_train_id(train_id)
    if not train:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                          detail=f"Train with ID {train_id} not found")
    
    # Now assign the train to the route using the MongoDB _id values
    assigned = await RouteModel.assign_train(route_id, train_id, str(train["_id"]))
    if not assigned:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                          detail="Failed to assign train to route")
    
    # Update the train's route reference
    await TrainModel.assign_route(train_id, route_id, str(route["_id"]))
    
    return {"message": f"Train {train_id} assigned to route {route_id} successfully"}

@router.get("/train/{train_id}", 
           response_model=Optional[RouteInDB],
           summary="Get route by train",
           description="Retrieve the route assigned to a specific train")
@handle_exceptions("retrieving route by train")
async def get_route_by_train(train_id: str = Path(..., description="The ID of the train")):
    """Get route by train ID"""
    route = await RouteModel.get_by_train_id(train_id)
    if not route:
        return None
    return RouteInDB(**route)

@router.get("/rfid/{rfid_tag}", 
           response_model=List[RouteInDB],
           summary="Get routes by RFID tag",
           description="Find routes that contain the specified RFID tag")
@handle_exceptions("retrieving routes by RFID")
async def get_routes_by_rfid(rfid_tag: str = Path(..., description="The RFID tag to search for")):
    """Find routes that contain a specific RFID tag"""
    routes = await RouteModel.find_routes_with_rfid_tag(rfid_tag)
    return [RouteInDB(**route) for route in routes]

