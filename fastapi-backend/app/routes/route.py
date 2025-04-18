"""
Route routes module.
Defines API endpoints for route operations.
"""
from fastapi import APIRouter, HTTPException, status, Body, Path, Query, Depends
from typing import List, Optional, Dict, Any
from app.models.route import RouteModel
from app.models.train import TrainModel
from app.schemas.route import RouteCreate, RouteUpdate, RouteInDB
from app.utils import handle_exceptions
from app.database import safe_db_operation

router = APIRouter()

@router.post("/", 
             response_model=RouteInDB, 
             status_code=status.HTTP_201_CREATED,
             summary="Create a new route",
             description="Create a new route with the provided information")
@handle_exceptions("creating route")
async def create_route(route: RouteCreate = Body(...)):
    """Create a new route"""
    # Implementation code here
    
    # This is just a simplified version for fixing errors
    route_id = await RouteModel.create(route.dict())
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
async def get_routes(limit: int = Query(100, gt=0, le=1000, description="Maximum number of routes to return"),
                   skip: int = Query(0, ge=0, description="Number of routes to skip")):
    """Get all routes with pagination"""
    routes = await RouteModel.get_all(limit=limit, skip=skip)
    return [RouteInDB(**route) for route in routes]

@router.get("/{id}", 
           response_model=RouteInDB,
           summary="Get a route by ID",
           description="Retrieve a route by its ID")
@handle_exceptions("retrieving route")
async def get_route(id: str = Path(..., description="The ID of the route to retrieve")):
    """Get a route by ID"""
    route = await RouteModel.get_by_id(id)
    if not route:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                          detail="Route not found")
    return RouteInDB(**route)

@router.get("/by-route-id/{route_id}", 
           response_model=RouteInDB,
           summary="Get a route by route_id",
           description="Retrieve a route by its route_id field")
@handle_exceptions("retrieving route by route_id")
async def get_route_by_route_id(route_id: str = Path(..., description="The route_id field value to search for")):
    """Get a route by route_id field"""
    route = await RouteModel.get_by_route_id(route_id)
    if not route:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                          detail=f"Route with route_id {route_id} not found")
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
    update_data = {k: v for k, v in route.dict().items() if v is not None}
    
    if not update_data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, 
                          detail="No valid update data provided")
    
    updated = await RouteModel.update(id, update_data)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                          detail="Route not found")
    
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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                          detail="Route not found")
    
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
    # First, check if both route and train exist
    route = await RouteModel.get_by_route_id(route_id)
    if not route:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                          detail=f"Route with route_id {route_id} not found")
    
    train = await TrainModel.get_by_train_id(train_id)
    if not train:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                          detail=f"Train with train_id {train_id} not found")
    
    # Now assign the train to the route using the MongoDB _id values
    assigned = await RouteModel.assign_train(route_id, train_id, str(train["_id"]))
    if not assigned:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                          detail="Failed to assign train to route")
    
    # Update the train's route reference
    await TrainModel.assign_route(str(train["_id"]), route_id, str(route["_id"]))
    
    return {"message": f"Train {train_id} assigned to route {route_id} successfully"}

@router.get("/tags/{rfid_tag}", 
           response_model=Dict[str, Any],
           summary="Find routes with a specific RFID tag",
           description="Find all routes that contain a specific RFID tag in their checkpoints")
@handle_exceptions("finding routes with RFID tag")
async def find_routes_with_rfid_tag(rfid_tag: str = Path(..., description="The RFID tag to search for")):
    """Find routes that have a specific RFID tag"""
    routes = await RouteModel.find_routes_with_rfid_tag(rfid_tag)
    
    if not routes:
        return {"found": False, "routes": []}
    
    return {
        "found": True,
        "routes": [RouteInDB(**route) for route in routes]
    }

# Comment out or remove the devices endpoint since DeviceModel doesn't exist
# If you need this endpoint, define the DeviceModel schema first
"""
@router.get("/devices", response_model=List[DeviceModel])
async def get_devices(location: Optional[str] = None, type: Optional[str] = None):
    return await safe_db_operation(
        lambda: get_devices_from_db(location, type),
        "Failed to fetch devices"
    )
"""

