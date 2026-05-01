# app/api/middleware/exchange_errors.py
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import traceback


class ExchangeErrorMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
        except Exception:
            return JSONResponse(
                status_code=500,
                content={"detail": "Erreur interne du serveur"},
            )


def register_exception_handlers(app):
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        error_str = str(exc).lower()
        if any(keyword in error_str for keyword in [
            "timeout", "requesttimeout", "exchangenotavailable",
            "dns", "connect", "binance.vision",
        ]):
            return JSONResponse(
                status_code=503,
                content={
                    "detail": "Timeout Binance testnet. Le serveur de test est lent/instable. Reessayez dans quelques minutes.",
                    "error_type": "exchange_timeout",
                },
            )
        if "authenticationerror" in error_str or "invalid api-key" in error_str:
            return JSONResponse(
                status_code=401,
                content={
                    "detail": "Cle API Binance invalide. Verifiez BINANCE_API_KEY dans .env ou regenerez vos cles testnet.",
                    "error_type": "exchange_auth",
                },
            )
        if "insufficientfunds" in error_str:
            return JSONResponse(
                status_code=400,
                content={
                    "detail": "Fonds insuffisants sur votre compte Binance.",
                    "error_type": "insufficient_funds",
                },
            )
        if "invalidorder" in error_str:
            return JSONResponse(
                status_code=400,
                content={
                    "detail": "Ordre invalide. Verifiez le symbole, la quantite et le prix.",
                    "error_type": "invalid_order",
                },
            )
        return JSONResponse(
            status_code=500,
            content={
                "detail": f"Erreur serveur: {str(exc)[:200]}",
                "error_type": "server_error",
            },
        )
