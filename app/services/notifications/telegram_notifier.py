# app/services/notifications/telegram_notifier.py
import httpx
from typing import Optional
from app.core.config import settings


class TelegramNotifier:

    def __init__(self, bot_token: str = None, chat_id: str = None):
        self.bot_token = bot_token or settings.TELEGRAM_BOT_TOKEN
        self.chat_id = chat_id or settings.TELEGRAM_CHAT_ID
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"

    async def send_message(self, text: str, parse_mode: str = "HTML") -> dict:
        if not self.bot_token or not self.chat_id:
            return {"error": "Telegram non configure"}
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/sendMessage",
                json={
                    "chat_id": self.chat_id,
                    "text": text,
                    "parse_mode": parse_mode,
                },
            )
            return response.json()

    async def notify_signal(self, symbol: str, action: str, price: float, strategy: str, confidence: float):
        emoji = "🟢" if action == "BUY" else "🔴"
        text = (
            f"{emoji} <b>Signal {action}</b>\n"
            f"Paire: <code>{symbol}</code>\n"
            f"Prix: <code>{price}</code>\n"
            f"Strategie: {strategy}\n"
            f"Confiance: {confidence*100:.0f}%"
        )
        return await self.send_message(text)

    async def notify_trade_open(self, symbol: str, side: str, price: float, quantity: float, sl: float, tp: float):
        emoji = "🟢" if side == "BUY" else "🔴"
        text = (
            f"{emoji} <b>Trade ouvert</b>\n"
            f"Paire: <code>{symbol}</code>\n"
            f"Side: {side}\n"
            f"Prix: <code>{price}</code>\n"
            f"Quantite: <code>{quantity}</code>\n"
            f"SL: <code>{sl}</code>\n"
            f"TP: <code>{tp}</code>"
        )
        return await self.send_message(text)

    async def notify_trade_close(self, symbol: str, side: str, entry: float, exit_price: float, pnl: float, reason: str):
        emoji = "✅" if pnl >= 0 else "❌"
        text = (
            f"{emoji} <b>Trade ferme</b>\n"
            f"Paire: <code>{symbol}</code>\n"
            f"Side: {side}\n"
            f"Entree: <code>{entry}</code>\n"
            f"Sortie: <code>{exit_price}</code>\n"
            f"PnL: <code>{pnl:.4f} USDT</code>\n"
            f"Raison: {reason}"
        )
        return await self.send_message(text)

    async def notify_backtest(self, strategy: str, symbol: str, trades: int, pnl: float, win_rate: float):
        emoji = "✅" if pnl >= 0 else "❌"
        text = (
            f"📊 <b>Backtest termine</b>\n"
            f"Strategie: {strategy}\n"
            f"Paire: <code>{symbol}</code>\n"
            f"Trades: {trades}\n"
            f"PnL: <code>{pnl:.2f} USDT</code> {emoji}\n"
            f"Win rate: {win_rate*100:.1f}%"
        )
        return await self.send_message(text)

    async def notify_error(self, error: str):
        text = f"⚠️ <b>Erreur Bot</b>\n<code>{error}</code>"
        return await self.send_message(text)


notifier = TelegramNotifier()
