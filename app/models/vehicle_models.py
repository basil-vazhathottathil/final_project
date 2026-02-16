# app/models/vehicle_models.py
"""
Pydantic models for vehicle management endpoints.
"""

from pydantic import BaseModel, Field  # type: ignore
from typing import Optional


class VehicleIdentifyRequest(BaseModel):
    vin: str = Field(..., min_length=17, max_length=17, description="17-character VIN")
    model: Optional[str] = Field(None, description="Optional vehicle model name")


class VehicleIdentifyResponse(BaseModel):
    vehicle_id: str
    is_new: bool
    vin: str
    model: Optional[str] = None


class VehicleSwitchRequest(BaseModel):
    vehicle_id: str


class VehicleResponse(BaseModel):
    id: str
    user_id: str
    vin: str
    model: Optional[str] = None
    created_at: str


class VehicleListResponse(BaseModel):
    vehicles: list[VehicleResponse]
