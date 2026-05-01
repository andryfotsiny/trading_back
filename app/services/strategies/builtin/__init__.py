# app/services/strategies/builtin/__init__.py
from app.services.strategies.builtin.rsi_oversold import RSIOversoldStrategy
from app.services.strategies.builtin.macd_crossover import MACDCrossoverStrategy
from app.services.strategies.builtin.sma_crossover import SMACrossoverStrategy
from app.services.strategies.builtin.bollinger_bounce import BollingerBounceStrategy
from app.services.strategies.builtin.grid_trading import GridTradingStrategy
from app.services.strategies.builtin.dca_bot import DCABotStrategy
from app.services.strategies.builtin.rsi_macd_combo import RSIMACDComboStrategy

STRATEGY_MAP = {
    "rsi_oversold": RSIOversoldStrategy,
    "macd_crossover": MACDCrossoverStrategy,
    "sma_crossover": SMACrossoverStrategy,
    "bollinger_bounce": BollingerBounceStrategy,
    "grid_trading": GridTradingStrategy,
    "dca_bot": DCABotStrategy,
    "rsi_macd_combo": RSIMACDComboStrategy,
}
