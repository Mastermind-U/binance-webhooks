from datetime import datetime

from pydantic import BaseModel


class Bar(BaseModel):
    time: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int


class Strategy(BaseModel):
    position_size: int
    order_action: str
    order_contracts: int
    order_price: float
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
