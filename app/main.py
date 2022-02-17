"""Main app file."""

import asyncio
import json
import math
import time
from datetime import datetime
from decimal import ROUND_FLOOR, Decimal, getcontext

from binance.client import AsyncClient
from config import Settings, get_settings
from exception_handlers import BINANCE_EXCEPTIONS, binance_exception_handler
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.encoders import jsonable_encoder
from loguru import logger
from models import WebhookData
from utils import get_quantity, get_step_size, get_wallet

logger.add("logs/app/main_{time:MM-DD}.log", level='DEBUG', rotation="00:00")


def set_app():
    """Create app."""
    getcontext().rounding = ROUND_FLOOR

    app = FastAPI(
        name="Binance-resolver",
        debug=get_settings().DEBUG,
    )

    for exc in BINANCE_EXCEPTIONS:
        app.exception_handler(exc)(binance_exception_handler)

    return app


app = set_app()


@app.on_event("startup")
async def set_up_binance():
    """Set up client as global var."""
    logger.info("Opening binance connection")
    settings = get_settings()
    app.state.binance = await AsyncClient.create(
        api_key=settings.API_KEY,
        api_secret=settings.SECRET_KEY,
    )
    fees = await app.state.binance.get_trade_fee()
    app.state.fees = {
        fee['symbol']: {
            'BUY': Decimal(fee['takerCommission']),
            'SELL': Decimal(fee['makerCommission']),
        } for fee in fees
    }


@app.on_event("shutdown")
async def close_binance():
    """Set up client as global var."""
    logger.info("Closing binance connection")
    await app.state.binance.close_connection()


@app.post('/webhook', status_code=status.HTTP_201_CREATED)
async def create_order(
    data: WebhookData,
    settings: Settings = Depends(get_settings),
):
    """Perform odred to binance, catch tradingview webhook."""
    binance: AsyncClient = app.state.binance

    if data.passphrase != settings.PASSPHRASE:
        raise HTTPException(
            detail="Invalid passphrase",
            status_code=401,
        )

    ticker = data.ticker
    start_time = time.time()
    acc, symbol, info = await asyncio.gather(
        binance.get_account(),
        binance.get_symbol_ticker(symbol=ticker),
        binance.get_symbol_info(symbol=ticker),
    )
    request_time = time.time() - start_time

    # TODO: Remove test wallet
    comissions = app.state.fees
    wallet = get_wallet(acc)
    usdt = cl - Decimal(685.0) if (cl := wallet['USDT']) > 0.01 else cl
    step_size = get_step_size(info)
    action = data.order_action.upper()
    unit_price = Decimal(symbol["price"])  # type: ignore
    precision = int(round(-math.log(step_size, 10), 0))
    qty = get_quantity(
        action, usdt, unit_price, precision,
        comissions[ticker], wallet, ticker,
    )

    try:
        response = await binance.create_test_order(
            symbol=data.ticker,
            side=action,
            type=binance.ORDER_TYPE_MARKET,
            quantity=qty,
        )
    finally:
        logger.info(json.dumps(jsonable_encoder({
            "start_time": datetime.fromtimestamp(start_time),
            "action": action,
            "qty": qty,
            "avaliable_usdt": usdt,
            "unit_price": unit_price,
            "precision": precision,
            "step_size": step_size,
            "wallet": wallet,
            "comissions": comissions,
            "req_time": request_time,
            "data": data,
        }), indent=4))

    logger.info({'result': response})
    if response:
        return {"status": 'OK'}

    raise HTTPException(500, "Order failed")
