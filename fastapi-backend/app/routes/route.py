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

@router.delete("/{id}", response_model=dict)
async def delete_route(id: str):
    """Delete a route"""
    deleted = await RouteModel.delete(id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Route not found")
    
    return {"message": "Route deleted successfully"}

@router.post("/", response_model=RouteInDB, status_code=status.HTTP_201_CREATED)
async def create_route(route: RouteCreate = Body(...)):
    try:
        route_id = await RouteModel.create(route.dict())
        created_route = await RouteModel.get_by_id(route_id)
        return RouteInDB(**created_route)
    except ValueError as ve:
        raise HTTPException(400, detail=str(ve))
    except Exception as e:
        raise HTTPException(500, detail=f"Server error: {str(e)}")

@router.put("/{id}", response_model=RouteInDB)
async def update_route(id: str, route: RouteUpdate = Body(...)):
    try:
        update_data = {k: v for k, v in route.dict().items() if v is not None}
        
        if not update_data:
            raise HTTPException(400, detail="No update data provided")
            
        updated = await RouteModel.update(id, update_data)
        if not updated:
            raise HTTPException(404, detail="Route not found")
            
        updated_route = await RouteModel.get_by_id(id)
        return RouteInDB(**updated_route)
    except ValueError as ve:
        raise HTTPException(400, detail=str(ve))
    except Exception as e:
        raise HTTPException(500, detail=f"Server error: {str(e)}")

