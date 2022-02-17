from decimal import Decimal

from fastapi import HTTPException


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
        if (avaliable_val := Decimal(balance["free"]))
    }


def get_quantity(
    side: str,  avaliable_usdt: Decimal,
    unit_price: Decimal,  precision: int,
    buy_fee: Decimal, sell_fee: Decimal,
    wallet: dict, ticker: str,
) -> Decimal:
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
        qty = wallet.get(ticker.replace('USDT', ''), Decimal(0.0)) * sell_fee
        qty = round(Decimal(qty), precision)
    else:
        HTTPException(400, "Action miss")

    return qty
