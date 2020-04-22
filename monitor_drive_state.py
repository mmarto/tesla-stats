#!/usr/bin/env python3

import pathlib
import configparser
import base64
import time
import sqlalchemy as sa
# import sshtunnel
# import mysql.connector
from client import TeslaClient
import logging
import pandas as pd

home_dir = pathlib.Path().home()
cfg_file = home_dir / 'config' / '.creds.cfg'

config = configparser.ConfigParser()
config.read(cfg_file)

creds = config['tesla.com']
logs = config['logs']

sqlite_creds = config['sqlite']


def create_engine(sqlite_creds, echo=False):
    conn_str = f"sqlite:///{sqlite_creds['host']}"
    return sa.create_engine(conn_str, echo=echo)


email = creds.get('username')
passwd = base64.b64decode(creds.get('password')).decode()

client = TeslaClient(email, passwd)

vehicles = client.get_vehicles()
vehicle = vehicles.pop()
print(vehicle.state)

engine = create_engine(sqlite_creds)
print(engine)

prev_active = True


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

logger = log_init(logs)

while True:
    try:
        state = vehicle.get_state()
        if state == 'asleep':
            logger.info('Asleep. Waiting for 5 minutes')
            prev_active = False
            time.sleep(5*60)
        else:
            logger.info(f'State: {state}')
            logger.info('Getting data...')
            drive_state = vehicle.get_drive_state()
            vehicle_state = vehicle.get_vehicle_state()
            shift_state = drive_state['shift_state']
            logger.info(vehicle_state['is_user_present'])
            speed = drive_state['speed']
            logger.info(drive_state)
            # logger.info(vehicle_state)
            data = pd.Series(drive_state).to_frame().T
            if speed is None:
                speed = 0.0
            else:
                float(speed) * 1.60934 # convert to km/h
            data.to_sql('drive_state', engine, index=False, if_exists='append')

            if shift_state is None and not vehicle_state['is_user_present'] and prev_active:
                logger.info('Shift state switched to None, sleeping for 21 minutes...')
                time.sleep(21*60)
            else:
                prev_active = True
                logger.info('Driving, sleeping for 1 min')
                time.sleep(60)
    except Exception as e:
        logger.exception(e)
        time.sleep(120)
