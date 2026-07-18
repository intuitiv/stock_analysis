from fastapi import APIRouter
from app.api.controllers import stock_controller

router = APIRouter()

router.include_router(
    stock_controller.router, 
    prefix="/stocks", 
    tags=["Stock Data"],
    responses={404: {"description": "Not found"}},
)
