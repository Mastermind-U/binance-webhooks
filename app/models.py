from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class WebhookData(BaseModel):
    passphrase: str
    time: datetime
    bar_time: datetime
    exchange: str
    ticker: str
    order_id: str
    order_action: str
