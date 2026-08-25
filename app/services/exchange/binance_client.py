# app/services/exchange/binance_client.py
import ccxt.async_support as ccxt
from typing import List, Dict, Optional
from app.services.exchange.base import BaseExchange

# Une instance ccxt par (cle, testnet) est partagee entre toutes les requetes:
# en creer une neuve a chaque appel forcait une nouvelle connexion TLS a
# Binance a chaque fois (2-3s), ce qui rendait les requetes lentes assez
# souvent annulees en plein vol par le frontend (resets cote nginx).
_exchange_cache: Dict[tuple, "ccxt.binance"] = {}


class BinanceClient(BaseExchange):

    def __init__(self, api_key: str, api_secret: str, testnet: bool = True):
        cache_key = (api_key, testnet)
        if cache_key not in _exchange_cache:
            instance = ccxt.binance({
                "apiKey": api_key,
                "secret": api_secret,
                "enableRateLimit": True,
                "timeout": 30000,
                "options": {"defaultType": "spot"},
            })
            if testnet:
                instance.set_sandbox_mode(True)
            _exchange_cache[cache_key] = instance
        self.exchange = _exchange_cache[cache_key]

    async def close(self):
        # Instance partagee et longue duree: ne pas fermer la connexion
        # sous les autres requetes en cours. Fermee au shutdown de l'app.
        pass

    async def get_balance(self) -> Dict:
        balance = await self.exchange.fetch_balance()
        return {
            "total": balance.get("total", {}),
            "free": balance.get("free", {}),
            "used": balance.get("used", {}),
        }

    async def get_ticker(self, symbol: str) -> Dict:
        raw = await self.exchange.publicGetTicker24hr({
            "symbol": symbol.replace("/", ""),
        })
        return {
            "symbol": symbol,
            "last": float(raw["lastPrice"]),
            "bid": float(raw["bidPrice"]),
            "ask": float(raw["askPrice"]),
            "high": float(raw["highPrice"]),
            "low": float(raw["lowPrice"]),
            "volume": float(raw["volume"]),
            "timestamp": int(raw["closeTime"]),
        }

    async def get_ohlcv(self, symbol: str, timeframe: str = "1h", limit: int = 100) -> List:
        raw = await self.exchange.publicGetKlines({
            "symbol": symbol.replace("/", ""),
            "interval": timeframe,
            "limit": limit,
        })
        return [
            {
                "timestamp": c[0],
                "open": float(c[1]),
                "high": float(c[2]),
                "low": float(c[3]),
                "close": float(c[4]),
                "volume": float(c[5]),
                "taker_buy_volume": float(c[9]),
            }
            for c in raw
        ]

    async def create_order(self, symbol: str, side: str, order_type: str, quantity: float, price: Optional[float] = None) -> Dict:
        order = await self.exchange.create_order(symbol, order_type, side, quantity, price)
        return {
            "id": order["id"],
            "symbol": order["symbol"],
            "side": order["side"],
            "type": order["type"],
            "quantity": order["amount"],
            "price": order["price"],
            "status": order["status"],
            "timestamp": order["timestamp"],
        }

    async def cancel_order(self, order_id: str, symbol: str) -> Dict:
        result = await self.exchange.cancel_order(order_id, symbol)
        return {"id": result["id"], "status": "cancelled"}

    async def get_open_orders(self, symbol: str = None) -> List:
        orders = await self.exchange.fetch_open_orders(symbol)
        return [
            {
                "id": o["id"],
                "symbol": o["symbol"],
                "side": o["side"],
                "type": o["type"],
                "quantity": o["amount"],
                "price": o["price"],
                "status": o["status"],
            }
            for o in orders
        ]

    async def get_order_status(self, order_id: str, symbol: str) -> Dict:
        order = await self.exchange.fetch_order(order_id, symbol)
        return {
            "id": order["id"],
            "symbol": order["symbol"],
            "side": order["side"],
            "type": order["type"],
            "quantity": order["amount"],
            "filled": order["filled"],
            "price": order["price"],
            "status": order["status"],
        }


async def close_all_exchanges():
    for instance in _exchange_cache.values():
        await instance.close()
    _exchange_cache.clear()
