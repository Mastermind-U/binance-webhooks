from binance.client import AsyncClient
from fastapi import HTTPException


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


def get_step_size(info):
    """Get step from info."""
    step_size = None
    for flt in info['filters']:
        if flt['filterType'] == "LOT_SIZE":
            step_size = float(flt['stepSize'])

    if not step_size:
        raise HTTPException(500, "Step failed")
    return step_size
