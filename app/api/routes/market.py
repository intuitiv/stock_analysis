from fastapi import APIRouter
from app.api.controllers import market_controller

router = APIRouter()

router.include_router(
    market_controller.router, 
    prefix="/market", 
    tags=["Market Data"],
    responses={404: {"description": "Not found"}},
)
