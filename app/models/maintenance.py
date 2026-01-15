from pydantic import BaseModel # type: ignore
from typing import Optional
from uuid import UUID
from datetime import date


class MaintenanceCreate(BaseModel):
    vehicle_id: UUID
    service_type: str
    service_date: Optional[date] = None
    odometer_km: Optional[int] = None
    notes: Optional[str] = None


class MaintenanceUpdate(BaseModel):
    service_date: Optional[date] = None
    odometer_km: Optional[int] = None
    notes: Optional[str] = None
    status: Optional[str] = None


class MaintenanceResponse(BaseModel):
    id: UUID
    vehicle_id: UUID
    service_type: str
    service_date: date
    odometer_km: Optional[int]
    next_due_km: Optional[int]
    next_due_date: Optional[date]
    status: str
