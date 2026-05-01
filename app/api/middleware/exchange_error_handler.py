# app/api/middleware/exchange_error_handler.py
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


def register_exchange_error_handlers(app: FastAPI):
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        error_str = str(exc).lower()

        if "requesttimeout" in type(exc).__name__.lower() or "timeout" in error_str:
            return JSONResponse(
                status_code=503,
                content={
                    "error": "timeout",
                    "message": "Binance testnet ne repond pas. Attendez quelques minutes et reessayez.",
                },
            )

        if "exchangenotavailable" in type(exc).__name__.lower() or "exchangeinfo" in error_str:
            return JSONResponse(
                status_code=503,
                content={
                    "error": "timeout",
                    "message": "Binance testnet ne repond pas. Attendez quelques minutes et reessayez.",
                },
            )

        if "authenticationerror" in type(exc).__name__.lower() or "invalid api-key" in error_str:
            return JSONResponse(
                status_code=401,
                content={
                    "error": "auth",
                    "message": "Cle API Binance invalide. Verifiez BINANCE_API_KEY dans .env.",
                },
            )

        if "networkerror" in type(exc).__name__.lower() or "dns" in error_str:
            return JSONResponse(
                status_code=503,
                content={
                    "error": "network",
                    "message": "Erreur reseau avec Binance. Verifiez votre connexion internet.",
                },
            )

        raise exc
