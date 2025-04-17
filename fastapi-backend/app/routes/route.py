"""
Route routes module.
Defines API endpoints for route operations.
"""
from fastapi import APIRouter, HTTPException, status, Body, Path, Query
from typing import List, Optional
from bson import ObjectId

from app.models.route import RouteModel
from app.schemas.route import RouteCreate, RouteUpdate, RouteInDB

router = APIRouter()

@router.get("/", 
            response_model=List[RouteInDB],
            summary="Get all routes",
            description="Retrieve a list of all registered routes")
async def get_routes():
    """Fetch all routes"""
    try:
        routes = await RouteModel.get_all()
        return routes
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching routes: {str(e)}")

@router.get("/{id}", 
            response_model=RouteInDB,
            summary="Get route by ID",
            description="Retrieve a specific route by its ID")
async def get_route(id: str = Path(..., description="The ID of the route to retrieve")):
    """Fetch a route by ID"""
    try:
        route = await RouteModel.get_by_id(id)
        if not route:
            raise HTTPException(status_code=404, detail="Route not found")
        return RouteInDB(**route)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching route: {str(e)}")

@router.get("/by-route-id/{route_id}", 
            response_model=RouteInDB,
            summary="Get route by route_id",
            description="Retrieve a specific route by its route_id field")
async def get_route_by_route_id(
    route_id: str = Path(..., description="The route_id field value to search for")
):
    """Fetch a route by route_id field"""
    try:
        route = await RouteModel.get_by_route_id(route_id)
        if not route:
            raise HTTPException(status_code=404, detail="Route not found")
        return RouteInDB(**route)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching route: {str(e)}")

@router.get("/train/{train_id}", 
            response_model=RouteInDB,
            summary="Get route by train ID",
            description="Retrieve a route assigned to a specific train")
async def get_route_by_train(
    train_id: str = Path(..., description="The ID of the train to find the route for")
):
    """Fetch a route by train ID"""
    try:
        route = await RouteModel.get_by_train_id(train_id)
        if not route:
            raise HTTPException(status_code=404, detail="Route not found for this train")
        return RouteInDB(**route)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching route: {str(e)}")

@router.post("/", 
             response_model=RouteInDB, 
             status_code=status.HTTP_201_CREATED,
             summary="Create a new route",
             description="Create a new route with the provided information including checkpoints")
async def create_route(route: RouteCreate = Body(...)):
    """Create a new route"""
    try:
        route_id = await RouteModel.create(route.dict())
        created_route = await RouteModel.get_by_id(route_id)
        if not created_route:
            raise HTTPException(status_code=500, detail="Failed to retrieve created route")
        return RouteInDB(**created_route)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error creating route: {str(e)}")

@router.put("/{id}", 
            response_model=RouteInDB,
            summary="Update an existing route",
            description="Update the details of an existing route by its ID")
async def update_route(
    id: str = Path(..., description="The ID of the route to update"),
    route: RouteUpdate = Body(...)
):
    """Update an existing route"""
    try:
        update_data = {k: v for k, v in route.dict().items() if v is not None}
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No valid update data provided")
        
        updated = await RouteModel.update(id, update_data)
        if not updated:
            raise HTTPException(status_code=404, detail="Route not found")
        
        updated_route = await RouteModel.get_by_id(id)
        if not updated_route:
            raise HTTPException(status_code=500, detail="Failed to retrieve updated route")
        
        return RouteInDB(**updated_route)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error updating route: {str(e)}")

@router.delete("/{id}", 
              response_model=dict,
              summary="Delete a route",
              description="Delete a route by its ID")
async def delete_route(id: str = Path(..., description="The ID of the route to delete")):
    """Delete a route by ID"""
    try:
        deleted = await RouteModel.delete(id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Route not found")
        
        return {"message": "Route deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting route: {str(e)}")

