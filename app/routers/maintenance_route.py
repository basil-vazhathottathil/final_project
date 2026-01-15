from fastapi import APIRouter, Depends # type: ignore
from app.auth.auth import get_current_user_id
from app.services.maintenance_service import *

router = APIRouter(prefix="/maintenance")

@router.get("/")
def list_maintenance(
    user_id: str = Depends(get_current_user_id),
):
    return list_maintenance_service(user_id)


@router.post("/")
def create_maintenance(
    payload: MaintenanceCreate,
    user_id: str = Depends(get_current_user_id),
):
    return create_maintenance_service(user_id, payload)


@router.put("/{maintenance_id}")
def update_maintenance(
    maintenance_id: str,
    payload: MaintenanceUpdate,
    user_id: str = Depends(get_current_user_id),
):
    return update_maintenance_service(user_id, maintenance_id, payload)


@router.delete("/{maintenance_id}")
def delete_maintenance(
    maintenance_id: str,
    user_id: str = Depends(get_current_user_id),
):
    return delete_maintenance_service(user_id, maintenance_id)
