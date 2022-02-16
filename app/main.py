"""Main app file."""

import asyncio
import math

from binance import enums
from binance.client import AsyncClient
from config import Settings, get_binance_client, get_settings
from exception_handlers import BINANCE_EXCEPTIONS, binance_exception_handler
from fastapi import Depends, FastAPI, HTTPException, status
from loguru import logger
from models import WebhookData
from utils import get_quantity, get_step_size, get_wallet

logger.add("logs/main.log", level='DEBUG', rotation="00:00")


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

    acc, symbol, info, comissions = asyncio.gather(
        binance.get_account(),
        binance.get_symbol_ticker(symbol=data.ticker),
        binance.get_symbol_info(symbol=data.ticker),
        binance.get_trade_fee(symbol=data.ticker),
    )

    logger.info(comissions)

    # TODO: Remove test wallet
    wallet = get_wallet(acc)
    avaliable_usdt = cl - 785.0 if (cl := wallet['USDT']) > 0.01 else cl
    step_size = get_step_size(info)
    buy_fee = (100 - float(comissions[0]['takerCommission'])) / 100
    sell_fee = (100 - float(comissions[0]['makerCommission'])) / 100
    action = data.strategy.order_action.upper()
    unit_price = float(symbol["price"])  # type: ignore
    precision = int(round(-math.log(step_size, 10), 0))
    qty = get_quantity(
        action, avaliable_usdt, unit_price, precision,
        buy_fee, sell_fee, wallet, data,
    )

    logger.info({
        "action": action,
        "qty": qty,
        "avaliable_usdt": avaliable_usdt,
        "unit_price": unit_price,
        "precision": precision,
        "step_size": step_size,
        "buy_fee": buy_fee,
        "comission": comissions,
        "sell_fee": sell_fee,
        "wallet": wallet,
    })

    response = await binance.create_order(
        symbol=data.ticker,
        side=action,
        type=enums.ORDER_TYPE_MARKET,
        quantity=qty,
    )

    logger.info({'result': response})
    if response:
        return {"status": 'OK'}

    raise HTTPException(500, "Order failed")
