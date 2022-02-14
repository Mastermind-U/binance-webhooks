"""Main app file."""

from binance import enums
from binance.client import AsyncClient
from config import Settings, get_binance_client, get_settings
from exception_handlers import BINANCE_EXCEPTIONS, binance_exception_handler
from fastapi import Depends, FastAPI, HTTPException, status
from loguru import logger
from models import WebhookData
import math

logger.add("logs/main.log", level='DEBUG')


def set_app():
    """Create app."""
    app = FastAPI(
        name="Binance-resolver",
        debug=get_settings().DEBUG,
    )

    for exc in BINANCE_EXCEPTIONS:
        app.exception_handler(exc)(binance_exception_handler)

    return app


app = set_app()


@app.post('/webhook', status_code=status.HTTP_201_CREATED)
async def create_order(
    data: WebhookData,
    settings: Settings = Depends(get_settings),
    binance: AsyncClient = Depends(get_binance_client),
):
    """Perform odred to binance, catch tradingview webhook."""
    if data.passphrase != settings.PASSPHRASE:
        raise HTTPException(
            detail="Invalid passphrase",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    side = data.strategy.order_action.upper()
    # quantity = data.strategy.order_contracts

    acc = await binance.get_account()
    symbol = await binance.get_symbol_ticker(symbol=data.ticker)
    info = await binance.get_symbol_info(symbol=data.ticker)

    step_size = .0

    for flt in info['filters']:
        if flt['filterType'] == "LOT_SIZE":
            step_size = float(flt['stepSize'])

    if not step_size:
        raise HTTPException(500, "Step failed")

    wallet = {
        balance['asset']: fee
        for balance in acc['balances']
        if (fee := float(balance["free"]))
    }
    avaliable_usdt = wallet['USDT']
    unit_price = float(symbol["price"]) * 0.9995
    precision = int(round(-math.log(step_size, 10), 0))

    if side == "BUY":
        qty = avaliable_usdt / unit_price
    elif side == "SELL":
        qty = wallet[data.ticker]  # avaliable currency
    else:
        HTTPException(400, "Action miss")

    qty = round(qty, precision)

    logger.info({
        "qty": qty,
        "avaliable_usdt": avaliable_usdt,
        "unit_price": unit_price,
        "precision": precision,
        "wallet": wallet,
    })
    response = await binance.create_order(
        symbol=data.ticker,
        side=side,
        type=enums.ORDER_TYPE_MARKET,
        quantity=qty,
    )
    logger.info({'data': data.dict(), 'result': response})
    if response:
        return {"status": 'OK'}

    raise HTTPException(500, "Order failed")
