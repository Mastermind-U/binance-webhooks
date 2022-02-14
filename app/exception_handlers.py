"""Exceptions handlers."""

from binance import exceptions
from fastapi import Request
from fastapi.responses import JSONResponse
from loguru import logger

BINANCE_EXCEPTIONS = (
    exceptions.BinanceAPIException,
    exceptions.BinanceRequestException,
    exceptions.BinanceOrderException,
    exceptions.BinanceOrderMinAmountException,
    exceptions.BinanceOrderMinPriceException,
    exceptions.BinanceOrderMinTotalException,
    exceptions.BinanceOrderUnknownSymbolException,
    exceptions.BinanceOrderInactiveSymbolException,
    exceptions.BinanceWebsocketUnableToConnect,
    exceptions.NotImplementedException,
)


async def binance_exception_handler(
    request: Request,
    exc: exceptions.BinanceAPIException,
):
    """Handle any binance exception."""
    logger.error(f"Catched binance error: {exc}")
    return JSONResponse(status_code=500, content={'detail': str(exc)})
