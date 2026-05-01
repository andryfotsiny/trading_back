# app/api/routes/bot.py
from fastapi import APIRouter, Depends
from app.db.models.user import User
from app.core.dependencies import get_current_user
from app.services.bot_runner import bot_cycle
from app.core.scheduler import scheduler

router = APIRouter()


@router.post("/run-now")
async def run_bot_now(current_user: User = Depends(get_current_user)):
    await bot_cycle()
    return {"detail": "Cycle execute manuellement"}


@router.get("/status")
def bot_status(current_user: User = Depends(get_current_user)):
    jobs = scheduler.get_jobs()
    if not jobs:
        return {"running": False}
    job = jobs[0]
    return {
        "running": True,
        "interval": "5 minutes",
        "next_run": str(job.next_run_time),
    }
