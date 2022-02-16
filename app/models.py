from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class Bar(BaseModel):
    time: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal


class Strategy(BaseModel):
    position_size: int
    order_action: str
    order_contracts: Decimal
    order_price: Decimal
    order_id: str
    market_position: str
    market_position_size: int
    prev_market_position: str
    prev_market_position_size: int


class WebhookData(BaseModel):
    passphrase: str
    time: datetime
    exchange: str
    ticker: str
    bar: Bar
    strategy: Strategy
