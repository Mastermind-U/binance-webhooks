from decimal import ROUND_FLOOR, Decimal, getcontext

from binance.client import AsyncClient
from fastapi import HTTPException
from models import WebhookData


async def get_spot_balance(client: AsyncClient) -> tuple[float, float]:
    """Get account total balance.

    return actives in usd and btc.
    """
    sum_btc = 0.0
    balances = await client.get_account()
    for _balance in balances["balances"]:
        asset = _balance["asset"]
        if float(_balance["free"]) != 0.0 or float(_balance["locked"]) != 0.0:
            try:
                btc_quantity =\
                    float(_balance["free"]) + float(_balance["locked"])
                if asset == "BTC":
                    sum_btc += btc_quantity
                else:
                    _price = await client.get_symbol_ticker(
                        symbol=asset + "BTC")
                    sum_btc += btc_quantity * float(_price["price"])
            except Exception:
                pass

    btc_price = await client.get_symbol_ticker(symbol="BTCUSDT")
    own_usd = sum_btc * float(btc_price["price"])
    return own_usd, sum_btc


def get_step_size(info) -> float:
    """Get step from info."""
    step_size = None
    for flt in info['filters']:
        if flt['filterType'] == "LOT_SIZE":
            step_size = float(flt['stepSize'])

    if not step_size:
        raise HTTPException(500, "Step failed")
    return step_size


def get_wallet(account) -> dict:
    """Get account balances as dict."""
    return {
        balance['asset']: avaliable_val for balance in account['balances']
        if (avaliable_val := float(balance["free"]))
    }


def get_quantity(
    side: str,  avaliable_usdt: float,
    unit_price: float,  precision: int,
    buy_fee: float, sell_fee: float,
    wallet: dict, data: WebhookData,
) -> float:
    """Compute quantity for order.

    Args:
        side (str): action buy or sell
        avaliable_usdt (float): balance
        unit_price (float): price in usdt for 1 unit
        precision (int): number of numbers
        buy_fee (float): fee market
        sell_fee (float): fee market
        wallet (dict): wallet dict
        data (WebhookData): data

    Returns:
        float: unit quantity
    """
    if side == "BUY":
        qty = avaliable_usdt / unit_price * buy_fee
        qty = round(qty, precision)
    elif side == "SELL":
        getcontext().rounding = ROUND_FLOOR
        qty = wallet[data.ticker.replace('USDT', '')] * sell_fee
        qty = round(Decimal(qty), precision)
    else:
        HTTPException(400, "Action miss")

    return qty
