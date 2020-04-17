#!/usr/bin/env python3

import sys
import datetime
import logging
import pathlib
import time
import configparser
import base64

from client import TeslaClient
from stats import transform_data, import_data

home_dir = pathlib.Path().home()
cfg_file = home_dir / 'config' / '.creds.cfg'

utils_path = home_dir / 'utils'
sys.path.append(utils_path.as_posix())

import db_utils as dbu

script = pathlib.Path(__file__)


def main():
    dt = datetime.datetime.now().date()
    config = configparser.ConfigParser()
    config.read(cfg_file)

    creds = config['tesla.com']
    logs = config['logs']
    logger = log_init(logs)
    logger.info(f'Start fetching data for {dt}')
    #
    # passwd = click.prompt('Password', hide_input=True)

    email = creds.get('username')
    passwd = base64.b64decode(creds.get('password')).decode()

    client = TeslaClient(email, passwd)

    vehicles = client.get_vehicles()

    vehicle = vehicles.pop()
    logger.info(f'id: {vehicle.id}')
    logger.info(f'name: {vehicle.display_name}')
    logger.info(f'state: {vehicle.state}')
    # state = vehicle.get_state()
    # print(state)
    if vehicle.state == 'asleep':
        asleep = True
        vehicle.wake_up()
        while asleep:
            time.sleep(5)
            state = vehicle.get_state()
            logger.info(state)
            if state == 'online':
                asleep = False

    vehicle_data = vehicle.get_vehicle_data()
    # print(vehicle_data)
    dfs = transform_data(vehicle_data)
    engine = dbu.get_dbconnection('MYSQL_TESLA', mysql_schema='mhristov$tesla_stats', echo=True)
    import_data(dfs, engine)


def log_init(logs):
    logger = logging.getLogger('tesla-stats')

    fmt = logging.Formatter("%(asctime)s %(name)s [%(levelname)s]: %(message)s")
    fh = logging.FileHandler(logs['tesla-stats'])
    fh.setFormatter(fmt)
    logger.addHandler(fh)
    ch = logging.StreamHandler()
    ch.setFormatter(fmt)
    logger.addHandler(ch)
    logger.setLevel(logging.INFO)

    return logger


center_display_state = {0: 'Off', 2: 'Normal On', 3: 'Charging Screen',
                        7: 'Sentry Mode', 8: 'Dog Mode'}

shorthand_fields = {'df': 'driver front', 'dr': 'driver rear', 'pf': 'passenger front',
                    'pr': 'passenger rear', 'ft': 'front trunk', 'rt': 'rear trunk'}


if __name__ == "__main__":
    main()