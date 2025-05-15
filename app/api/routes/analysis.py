from fastapi import APIRouter
from app.api.controllers import analysis_controller

router = APIRouter()

router.include_router(
    analysis_controller.router, 
    prefix="/analysis", 
    tags=["Analysis & Insights"],
    responses={404: {"description": "Not found"}},
)
