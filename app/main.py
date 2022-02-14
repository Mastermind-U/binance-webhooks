"""Main app file."""

from binance import enums
from binance.client import AsyncClient
from config import Settings, get_binance_client, get_settings
from exception_handlers import BINANCE_EXCEPTIONS, binance_exception_handler
from fastapi import Depends, FastAPI, HTTPException, status
from loguru import logger
from models import WebhookData
from utils import get_spot_balance

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

    available_usd, avaliable_btc = await get_spot_balance(binance)
    price = await binance.get_symbol_ticker(symbol=data.ticker)

    info = await binance.get_symbol_info(symbol=data.ticker)
    buy_quantity = round(
        available_usd / float(price['price']), info['quotePrecision'])

    logger.info((available_usd, avaliable_btc, price, buy_quantity))

    response = await binance.create_test_order(
        symbol=data.ticker,
        side=side,
        type=enums.ORDER_TYPE_MARKET,
        quantity=buy_quantity,
    )
    logger.info({'data': data.dict(), 'result': response})
    if response:
        return {"status": 'OK'}

    raise HTTPException(500, "Order failed")
