from fastapi import APIRouter, Depends
from uuid import UUID

from app.auth.auth import verify_token
from app.models.maintenance import (
    MaintenanceCreate,
    MaintenanceUpdate,
)
from app.services.maintenance_service import (
    create_maintenance,
    list_maintenance,
    list_maintenance_by_vehicle,
    update_maintenance,
    delete_maintenance,
)

router = APIRouter(prefix="/maintenance", tags=["Maintenance"])


@router.post("/")
def add_maintenance(payload: MaintenanceCreate, user=Depends(verify_token)):
    return create_maintenance(user["sub"], payload)


@router.get("/")
def get_all(user=Depends(verify_token)):
    return list_maintenance(user["sub"])


@router.get("/vehicle/{vehicle_id}")
def get_by_vehicle(vehicle_id: UUID, user=Depends(verify_token)):
    return list_maintenance_by_vehicle(user["sub"], vehicle_id)


@router.put("/{maintenance_id}")
def edit(
    maintenance_id: UUID,
    payload: MaintenanceUpdate,
    user=Depends(verify_token),
):
    return update_maintenance(user["sub"], maintenance_id, payload)


@router.delete("/{maintenance_id}")
def remove(maintenance_id: UUID, user=Depends(verify_token)):
    return delete_maintenance(user["sub"], maintenance_id)
