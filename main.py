# main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes.auth import router as auth_router
from app.api.routes.user import router as user_router
from app.api.routes.exchanges import router as exchanges_router
from app.api.routes.market_data import router as market_data_router
from app.api.routes.signals import router as signals_router
from app.api.routes.strategies.crud import router as strategies_crud_router
from app.api.routes.strategies.activation import router as strategies_activation_router
from app.api.routes.trading.portfolio import router as trading_portfolio_router
from app.api.routes.trading.orders import router as trading_orders_router
from app.api.routes.trading.positions import router as trading_positions_router
from app.api.routes.backtest.run import router as backtest_run_router
from app.api.routes.backtest.results import router as backtest_results_router
from app.api.routes.backtest.optimizer import router as optimizer_router
from app.api.routes.notifications import router as notifications_router
from app.api.routes.ai import router as ai_router
from app.api.routes.bot import router as bot_router
from app.api.routes.dashboard import router as dashboard_router
from app.core.scheduler import scheduler
from app.services.bot_runner import bot_cycle
import logging
from app.api.routes.calendar import router as calendar_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("trading_bot")


@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler.add_job(bot_cycle, "interval", minutes=5, id="bot_cycle", replace_existing=True)
    scheduler.start()
    logger.info("Bot demarre - cycle toutes les 5 minutes")
    yield
    scheduler.shutdown()
    logger.info("Bot arrete")


app = FastAPI(title="Trading Bot API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
app.include_router(user_router, prefix="/api/users", tags=["users"])
app.include_router(exchanges_router, prefix="/api/exchanges", tags=["exchanges"])
app.include_router(market_data_router, prefix="/api/market", tags=["market"])
app.include_router(signals_router, prefix="/api/signals", tags=["signals"])
app.include_router(strategies_crud_router, prefix="/api/strategies", tags=["strategies"])
app.include_router(strategies_activation_router, prefix="/api/strategies", tags=["strategies-run"])
app.include_router(trading_portfolio_router, prefix="/api/trading", tags=["trading-risk"])
app.include_router(trading_orders_router, prefix="/api/trading", tags=["trading-orders"])
app.include_router(trading_positions_router, prefix="/api/trading", tags=["trading-real"])
app.include_router(backtest_run_router, prefix="/api/backtest", tags=["backtest"])
app.include_router(backtest_results_router, prefix="/api/backtest", tags=["backtest"])
app.include_router(optimizer_router, prefix="/api/optimizer", tags=["optimizer"])
app.include_router(notifications_router, prefix="/api/notifications", tags=["notifications"])
app.include_router(ai_router, prefix="/api/ai", tags=["ai"])
app.include_router(bot_router, prefix="/api/bot", tags=["bot"])
app.include_router(dashboard_router, prefix="/api/dashboard", tags=["dashboard"])
app.include_router(calendar_router, prefix="/api/calendar", tags=["calendar"])

@app.get("/")
def root():
    return {"status": "ok", "service": "trading_bot", "bot": "running every 5 min"}


@app.get("/health")
def health():
    jobs = scheduler.get_jobs()
    return {"status": "healthy", "bot_active": len(jobs) > 0, "next_run": str(jobs[0].next_run_time) if jobs else None}
