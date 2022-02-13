import os

from pydantic import BaseSettings
from functools import lru_cache
from hvac import Client


class Settings(BaseSettings):
    DEBUG: bool
    API_KEY: str
    SECRET_KEY: str


@lru_cache
def get_settings():
    client = Client(
        url='http://vault:8200',
        token=os.environ['VAULT_ROOT_TOKEN'],
    )
    if not client.is_authenticated():
        raise Exception

    data = client.secrets.kv.v1.read_secret(
        path='BINANCE',
        mount_point='kv',
    )

    return Settings(
        API_KEY=data['data']['API_KEY'],
        SECRET_KEY=data['data']['API_KEY'],
    )
