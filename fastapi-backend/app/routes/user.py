"""
User routes module.
Defines API endpoints for user operations and authentication.
"""
from fastapi import APIRouter, HTTPException, status, Body, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from typing import List
from datetime import timedelta
from bson import ObjectId

from app.models.user import UserModel
from app.schemas.user import UserCreate, UserUpdate, UserInDB, Token
from app.utils import create_access_token
from app.config import ACCESS_TOKEN_EXPIRE_MINUTES

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/users/token")

@router.get("/", response_model=List[UserInDB])
async def get_users():
    """Get all users"""
    users = await UserModel.get_all()
    return users

@router.get("/{id}", response_model=UserInDB)
async def get_user(id: str):
    """Get a user by ID"""
    user = await UserModel.get_by_id(id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.post("/", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate = Body(...)):
    """Create a new user"""
    # Check if username already exists
    existing_user = await UserModel.get_by_username(user.username)
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    user_id = await UserModel.create(user.dict())
    return {"id": user_id, "message": "User created successfully"}

@router.put("/{id}", response_model=dict)
async def update_user(id: str, user: UserUpdate = Body(...)):
    """Update a user"""
    # Filter out None values
    user_data = {k: v for k, v in user.dict().items() if v is not None}
    
    if not user_data:
        raise HTTPException(status_code=400, detail="No valid update data provided")
    
    # Check if username already exists if username is being updated
    if "username" in user_data:
        existing_user = await UserModel.get_by_username(user_data["username"])
        if existing_user and str(existing_user["_id"]) != id:
            raise HTTPException(status_code=400, detail="Username already taken")
    
    updated = await UserModel.update(id, user_data)
    if not updated:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"message": "User updated successfully"}

@router.delete("/{id}", response_model=dict)
async def delete_user(id: str):
    """Delete a user"""
    deleted = await UserModel.delete(id)
    if not deleted:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"message": "User deleted successfully"}

@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """Login and get access token"""
    user = await UserModel.authenticate(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"], "id": str(user["_id"])},
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}
