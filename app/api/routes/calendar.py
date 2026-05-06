# app/api/routes/calendar.py
from fastapi import APIRouter, Depends, Query
from app.db.models.user import User
from app.core.dependencies import get_current_user
from app.services.calendar.fear_greed import get_fear_greed_index
from app.services.calendar.economic_calendar import (
    get_economic_calendar,
    get_high_impact_events,
    should_trade,
)

router = APIRouter()


@router.get("/fear-greed")
async def fear_greed(
    limit: int = Query(default=1, le=30),
    current_user: User = Depends(get_current_user),
):
    return await get_fear_greed_index(limit)


@router.get("/fear-greed/history")
async def fear_greed_history(
    current_user: User = Depends(get_current_user),
):
    return await get_fear_greed_index(limit=30)


@router.get("/economic")
async def economic_calendar(
    from_date: str = Query(default=None),
    to_date: str = Query(default=None),
    country: str = Query(default=None),
    importance: int = Query(default=None, ge=1, le=3),
    current_user: User = Depends(get_current_user),
):
    return await get_economic_calendar(from_date, to_date, country, importance)


@router.get("/economic/high-impact")
async def high_impact_events(
    hours: int = Query(default=4, ge=1, le=24),
    current_user: User = Depends(get_current_user),
):
    return await get_high_impact_events(hours)


@router.get("/should-trade")
async def check_should_trade(
    current_user: User = Depends(get_current_user),
):
    return await should_trade()
