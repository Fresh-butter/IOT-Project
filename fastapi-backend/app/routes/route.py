"""
Route routes module.
Defines API endpoints for route operations.
"""
from fastapi import APIRouter, HTTPException, status, Body, Depends
from typing import List
from bson import ObjectId

from app.models.route import RouteModel
from app.schemas.route import RouteCreate, RouteUpdate, RouteInDB

router = APIRouter()

@router.get("/", response_model=List[RouteInDB])
async def get_routes():
    """Get all routes"""
    routes = await RouteModel.get_all()
    return routes

@router.get("/{id}", response_model=RouteInDB)
async def get_route(id: str):
    """Get a route by ID"""
    route = await RouteModel.get_by_id(id)
    if not route:
        raise HTTPException(status_code=404, detail="Route not found")
    return route

@router.get("/train/{train_id}", response_model=RouteInDB)
async def get_route_by_train(train_id: str):
    """Get a route by train ID"""
    route = await RouteModel.get_by_train_id(train_id)
    if not route:
        raise HTTPException(status_code=404, detail="Route not found for this train")
    return route

@router.post("/", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_route(route: RouteCreate = Body(...)):
    """Create a new route"""
    route_id = await RouteModel.create(route.dict())
    return {"id": route_id, "message": "Route created successfully"}

@router.put("/{id}", response_model=dict)
async def update_route(id: str, route: RouteUpdate = Body(...)):
    """Update a route"""
    # Filter out None values
    route_data = {k: v for k, v in route.dict().items() if v is not None}
    
    if not route_data:
        raise HTTPException(status_code=400, detail="No valid update data provided")
    
    updated = await RouteModel.update(id, route_data)
    if not updated:
        raise HTTPException(status_code=404, detail="Route not found")
    
    return {"message": "Route updated successfully"}

@router.delete("/{id}", response_model=dict)
async def delete_route(id: str):
    """Delete a route"""
    deleted = await RouteModel.delete(id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Route not found")
    
    return {"message": "Route deleted successfully"}
