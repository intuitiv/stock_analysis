from fastapi import APIRouter
from app.api.controllers import auth_controller

router = APIRouter()

# Include the controller routes with a prefix and tags
router.include_router(
    auth_controller.router, 
    prefix="/auth", 
    tags=["Authentication"],
    responses={404: {"description": "Not found"}}, # Example common response
)

# You could add other top-level routes related to auth here if needed
