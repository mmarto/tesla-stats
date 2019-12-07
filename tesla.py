#!/usr/bin/env python3
import requests
import click
import pandas as pd
from collections import defaultdict
import datetime
import sqlalchemy as sa
import logging
import pathlib
import time
import configparser
import base64

from client import TeslaClient
from stats import transform_data, import_data

TESLA_API_BASE_URL = 'https://owner-api.teslamotors.com/'
TOKEN_URL = TESLA_API_BASE_URL + 'oauth/token'
API_URL = TESLA_API_BASE_URL + 'api/1'

OAUTH_CLIENT_ID = '81527cff06843c8634fdc09e8ac0abefb46ac849f38fe1e431c2ef2106796384'
OAUTH_CLIENT_SECRET = 'c7257eb71a564034f9419ee651c7d0e5f7aa6bfbd18bafb5c5c033b093bb2fa3'

home_dir = pathlib.Path().home()
cfg_file = home_dir / 'config' / '.creds.cfg'

script = pathlib.Path(__file__)
logger = logging.getLogger(script.name)

fmt = logging.Formatter("%(asctime)s %(name)s [%(levelname)s]: %(message)s")
fh = logging.FileHandler(script.with_suffix('.log'))
fh.setFormatter(fmt)
logger.addHandler(fh)
ch = logging.StreamHandler()
ch.setFormatter(fmt)
logger.addHandler(ch)
logger.setLevel(logging.INFO)

dt = datetime.datetime.now().date()

logger.info(f'Start fetching data for {dt}')


def main():
    config = configparser.ConfigParser()
    config.read(cfg_file)

    creds = config['tesla.com']

    #
    # passwd = click.prompt('Password', hide_input=True)

    email = creds.get('username')
    passwd = base64.b64decode(creds.get('password')).decode()

    client = TeslaClient(email, passwd)

    vehicles = client.get_vehicles()

    vehicle = vehicles.pop()
    print(f'id: {vehicle.id}')
    print(f'name: {vehicle.display_name}')
    print(f'state: {vehicle.state}')
    # state = vehicle.get_state()
    # print(state)
    if vehicle.state == 'asleep':
        asleep = True
        vehicle.wake_up()
        while asleep:
            time.sleep(5)
            state = vehicle.get_state()
            print(state)
            if state == 'online':
                asleep = False

    vehicle_data = vehicle.get_vehicle_data()
    print(vehicle_data)
    dfs = transform_data(vehicle_data)
    import_data(dfs)


if __name__ == "__main__":
    main()
