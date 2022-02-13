import os
from functools import lru_cache

from hvac import Client
from pydantic import BaseSettings


class Settings(BaseSettings):
    DEBUG: bool
    API_KEY: str
    SECRET_KEY: str
    PASSPHRASE: str


@lru_cache
def get_settings():
    """Get settings from vault and env."""
    client = Client(
        url='http://vault:8200',
        token=os.environ['VAULT_ROOT_TOKEN'],
    )
    if not client.is_authenticated():
        raise Exception('Vault auth error')

    binance_data = client.secrets.kv.v1.read_secret(
        path='BINANCE',
        mount_point='kv',
    )['data']

    return Settings(
        API_KEY=binance_data['API_KEY'],
        SECRET_KEY=binance_data['API_SECRET'],
        PASSPHRASE=binance_data['PASSPHRASE'],
    )
