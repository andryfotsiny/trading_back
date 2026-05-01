# app/services/exchange/factory.py
from app.services.exchange.base import BaseExchange
from app.services.exchange.binance_client import BinanceClient
from app.core.config import settings


def create_exchange(
    exchange_name: str = None,
    api_key: str = None,
    api_secret: str = None,
    testnet: bool = None,
) -> BaseExchange:
    name = (exchange_name or settings.EXCHANGE_NAME).lower()
    key = api_key or settings.BINANCE_API_KEY
    secret = api_secret or settings.BINANCE_API_SECRET
    is_testnet = testnet if testnet is not None else settings.BINANCE_TESTNET

    if name == "binance":
        return BinanceClient(api_key=key, api_secret=secret, testnet=is_testnet)

    raise ValueError(f"Exchange non supporte: {name}")
