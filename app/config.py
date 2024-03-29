"""Configs for app."""

import os
from functools import lru_cache

from binance.client import AsyncClient
from hvac import Client
from loguru import logger
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

    if client.sys.is_sealed():
        logger.warning('Vault sealed, unsealing...')
        client.sys.submit_unseal_key(os.environ["VAULT_KEY"])

    if not client.is_authenticated():
        raise Exception('Vault auth error')

    binance_data = client.secrets.kv.v1.read_secret('BINANCE', 'kv')['data']

    return Settings(
        API_KEY=binance_data['API_KEY'],
        SECRET_KEY=binance_data['API_SECRET'],
        PASSPHRASE=binance_data['PASSPHRASE'],
    )
