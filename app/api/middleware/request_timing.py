# app/api/middleware/request_timing.py
import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request


class RequestTimingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.time()
        response = await call_next(request)
        duration = time.time() - start
        response.headers["X-Process-Time"] = str(round(duration, 4))
        return response
