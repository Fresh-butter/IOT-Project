"""
Route routes module.
Defines API endpoints for route operations.
"""
from fastapi import APIRouter, HTTPException, status, Body, Path, Query, Depends
from typing import List, Optional, Dict, Any
from bson import ObjectId
from datetime import datetime

from app.models.route import RouteModel
from app.models.train import TrainModel
from app.schemas.route import RouteCreate, RouteUpdate, RouteInDB
from app.utils import handle_exceptions
from app.config import get_current_ist_time

router = APIRouter()

@router.get("/", 
            response_model=List[RouteInDB],
            summary="Get all routes",
            description="Retrieve a list of all registered routes with pagination")
@handle_exceptions("fetching routes")
async def get_routes(
    limit: Optional[int] = Query(1000, ge=1, le=1000, description="Maximum number of routes to return"),
    skip: Optional[int] = Query(0, ge=0, description="Number of routes to skip")
):
    """Fetch all routes with pagination"""
    routes = await RouteModel.get_all(limit=limit, skip=skip)
    return [RouteInDB(**route) for route in routes]

@router.get("/{id}", 
            response_model=RouteInDB,
            summary="Get route by ID",
            description="Retrieve a specific route by its ID")
@handle_exceptions("fetching route")
async def get_route(id: str = Path(..., description="The ID of the route to retrieve")):
    """Fetch a route by ID"""
    route = await RouteModel.get_by_id(id)
    if not route:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                          detail="Route not found")
    return RouteInDB(**route)

@router.get("/by-route-id/{route_id}", 
            response_model=RouteInDB,
            summary="Get route by route_id",
            description="Retrieve a specific route by its route_id field")
@handle_exceptions("fetching route by route_id")
async def get_route_by_route_id(
    route_id: str = Path(..., description="The route_id field value to search for")
):
    """Fetch a route by route_id field"""
    route = await RouteModel.get_by_route_id(route_id)
    if not route:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                          detail="Route not found")
    return RouteInDB(**route)

@router.get("/train/{train_id}", 
            response_model=RouteInDB,
            summary="Get route by train ID",
            description="Retrieve a route assigned to a specific train")
@handle_exceptions("fetching route by train")
async def get_route_by_train(
    train_id: str = Path(..., description="The ID of the train to find the route for")
):
    """Fetch a route by train ID"""
    route = await RouteModel.get_by_train_id(train_id)
    if not route:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                          detail="Route not found for this train")
    return RouteInDB(**route)

@router.get("/rfid/{rfid_tag}", 
            response_model=List[RouteInDB],
            summary="Find routes with RFID tag",
            description="Find routes that include a specific RFID tag in their checkpoints")
@handle_exceptions("finding routes with RFID tag")
async def find_routes_with_rfid(
    rfid_tag: str = Path(..., description="The RFID tag to search for")
):
    """Find routes containing a specific RFID tag"""
    routes = await RouteModel.find_routes_with_rfid_tag(rfid_tag)
    return [RouteInDB(**route) for route in routes]

@router.post("/", 
             response_model=RouteInDB, 
             status_code=status.HTTP_201_CREATED,
             summary="Create a new route",
             description="Create a new route with the provided information including checkpoints")
@handle_exceptions("creating route")
async def create_route(route: RouteCreate = Body(...)):
    """Create a new route"""
    route_dict = route.dict()
    
    # Set default start_time if not provided
    if "start_time" not in route_dict or route_dict["start_time"] is None:
        route_dict["start_time"] = get_current_ist_time()
    
    # Handle train reference if provided
    if "assigned_train_id" in route_dict and route_dict["assigned_train_id"]:
        # Check if train exists
        train = await TrainModel.get_by_train_id(route_dict["assigned_train_id"])
        if not train:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, 
                              detail=f"Train with ID {route_dict['assigned_train_id']} not found")
        route_dict["assigned_train_ref"] = str(train["_id"])
    
    route_id = await RouteModel.create(route_dict)
    created_route = await RouteModel.get_by_id(route_id)
    if not created_route:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                          detail="Failed to retrieve created route")
    return RouteInDB(**created_route)

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
    update_data = {k: v for k, v in route.dict().items() if v is not None}
    
    if not update_data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, 
                          detail="No valid update data provided")
    
    # Handle train reference if train ID is being updated
    if "assigned_train_id" in update_data:
        if update_data["assigned_train_id"]:
            # Check if train exists
            train = await TrainModel.get_by_train_id(update_data["assigned_train_id"])
            if not train:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, 
                                  detail=f"Train with ID {update_data['assigned_train_id']} not found")
            update_data["assigned_train_ref"] = str(train["_id"])
        else:
            # If train_id is set to null, also set reference to null
            update_data["assigned_train_ref"] = None
    
    updated = await RouteModel.update(id, update_data)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                          detail="Route not found")
    
    updated_route = await RouteModel.get_by_id(id)
    return RouteInDB(**updated_route)

@router.put("/{route_id}/assign-train/{train_id}", 
           response_model=RouteInDB,
           summary="Assign train to route",
           description="Assign a train to a route")
@handle_exceptions("assigning train to route")
async def assign_train_to_route(
    route_id: str = Path(..., description="The ID of the route"),
    train_id: str = Path(..., description="The ID of the train to assign")
):
    """Assign a train to a route"""
    # Find the train first
    train = await TrainModel.get_by_id(train_id)
    if not train:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                          detail=f"Train with ID {train_id} not found")
    
    # Find the route
    route = await RouteModel.get_by_id(route_id)
    if not route:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                          detail=f"Route with ID {route_id} not found")
    
    # Assign the train to the route
    await RouteModel.assign_train(route_id, train["train_id"], str(train["_id"]))
    
    # Also update the train to reference this route
    await TrainModel.assign_route(train_id, route["route_id"], str(route["_id"]))
    
    # Get updated route data
    updated_route = await RouteModel.get_by_id(route_id)
    return RouteInDB(**updated_route)

@router.delete("/{id}", 
              response_model=Dict[str, str],
              summary="Delete a route",
              description="Delete a route by its ID")
@handle_exceptions("deleting route")
async def delete_route(id: str = Path(..., description="The ID of the route to delete")):
    """Delete a route by ID"""
    # Check if route exists
    route = await RouteModel.get_by_id(id)
    if not route:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                          detail="Route not found")
    
    # If the route has an assigned train, update the train's references
    if route.get("assigned_train_id") and route.get("assigned_train_ref"):
        train = await TrainModel.get_by_id(str(route["assigned_train_ref"]))
        if train and train.get("current_route_id") == route["route_id"]:
            # Clear the train's route references
            await TrainModel.update(str(train["_id"]), {
                "current_route_id": None,
                "current_route_ref": None
            })
    
    # Delete the route
    deleted = await RouteModel.delete(id)
    
    return {"message": "Route deleted successfully"}

