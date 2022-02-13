"""Main app file."""

from binance import enums, exceptions
from binance.client import AsyncClient
from config import Settings, get_settings
from fastapi import Depends, FastAPI, HTTPException, Request, status
from models import WebhookData

app = FastAPI(
    name="Binance-resolver",
    debug=get_settings().DEBUG,
)


binance_exceptions = (
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
    raise HTTPException(
        status.HTTP_500_INTERNAL_SERVER_ERROR, str(exc)
    ) from exc


for exc in binance_exceptions:
    app.exception_handler(exc)


async def get_binance_client(settings: Settings = Depends(get_settings)):
    """Get binance client via dependency."""
    client = AsyncClient.create(
        api_key=settings.API_KEY,
        api_secret=settings.SECRET_KEY,
    )
    try:
        yield client
    finally:
        client.close()


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
    quantity = data.strategy.order_contracts

    response = await binance.create_order(
        symbol=data.ticker,
        side=side,
        type=enums.ORDER_TYPE_MARKET,
        quantity=quantity,
    )

    if response:
        return {"status": 'OK'}

    raise HTTPException(
        status.HTTP_500_INTERNAL_SERVER_ERROR, "Order failed")
