# app/services/market_data/websocket_stream.py
import asyncio
import json
from typing import Callable, Optional
import websockets


class BinanceWebSocket:

    def __init__(self, testnet: bool = True):
        if testnet:
            self.base_url = "wss://stream.testnet.binance.vision/ws"
        else:
            self.base_url = "wss://stream.binance.com:9443/ws"
        self.running = False

    async def subscribe_ticker(self, symbol: str, callback: Callable):
        stream = symbol.lower().replace("/", "") + "@ticker"
        url = f"{self.base_url}/{stream}"
        self.running = True
        async with websockets.connect(url) as ws:
            while self.running:
                try:
                    msg = await asyncio.wait_for(ws.recv(), timeout=30)
                    data = json.loads(msg)
                    ticker = {
                        "symbol": symbol,
                        "price": float(data.get("c", 0)),
                        "high": float(data.get("h", 0)),
                        "low": float(data.get("l", 0)),
                        "volume": float(data.get("v", 0)),
                    }
                    await callback(ticker)
                except asyncio.TimeoutError:
                    continue
                except Exception:
                    break

    async def subscribe_kline(self, symbol: str, timeframe: str, callback: Callable):
        stream = symbol.lower().replace("/", "") + f"@kline_{timeframe}"
        url = f"{self.base_url}/{stream}"
        self.running = True
        async with websockets.connect(url) as ws:
            while self.running:
                try:
                    msg = await asyncio.wait_for(ws.recv(), timeout=30)
                    data = json.loads(msg)
                    k = data.get("k", {})
                    candle = {
                        "symbol": symbol,
                        "timeframe": timeframe,
                        "open": float(k.get("o", 0)),
                        "high": float(k.get("h", 0)),
                        "low": float(k.get("l", 0)),
                        "close": float(k.get("c", 0)),
                        "volume": float(k.get("v", 0)),
                        "closed": k.get("x", False),
                    }
                    await callback(candle)
                except asyncio.TimeoutError:
                    continue
                except Exception:
                    break

    def stop(self):
        self.running = False
