#!/usr/bin/env python3

import pathlib
import configparser
import base64
import time
import sqlalchemy as sa
import sshtunnel
import mysql.connector
from client import TeslaClient

home_dir = pathlib.Path().home()
cfg_file = home_dir / 'config' / '.creds.cfg'

config = configparser.ConfigParser()
config.read(cfg_file)

creds = config['tesla.com']

mysql_creds = config['mysql']


def create_engine(creds, echo=False):
    creds['password'] = base64.b64decode(creds['password']).decode()
    conn_str = f"mysql+mysqlconnector://{creds['username']}:{creds['password']}@{creds['host']}/{creds['schema']}"
    return sa.create_engine(conn_str, pool_recycle=280, echo=echo)


engine = create_engine(mysql_creds)
print(engine)
print(engine.execute('select 1').scalar())
exit()
email = creds.get('username')
passwd = base64.b64decode(creds.get('password')).decode()

client = TeslaClient(email, passwd)

vehicles = client.get_vehicles()
vehicle = vehicles.pop()
print(vehicle.state)

prev_active = True

sshtunnel.SSH_TIMEOUT = 5.0
sshtunnel.TUNNEL_TIMEOUT = 5.0
with sshtunnel.SSHTunnelForwarder(
    ('ssh.pythonanywhere.com'),
    ssh_username='mhristov', ssh_password='yngwie77',
    remote_bind_address=('mhristov.mysql.pythonanywhere-services.com', 3306)
) as tunnel:
    connection = mysql.connector.connect(
        user='mhristov', password='mica2019db',
        host='127.0.0.1', port=tunnel.local_bind_port,
        database='mhristov$tesla_stats', use_pure=True
    )
    cur = connection.cursor()
    cur.execute('select 1')
    print(cur.fetchone())
    connection.close()




while True:

    state = vehicle.get_state()
    if state == 'asleep':
        print('Asleep. Waiting for 5 minutes')
        prev_active = False
        time.sleep(5*60)
    else:
        print('Getting data...')
        drive_state = vehicle.get_drive_state()
        charge_state = vehicle.get_charge_state()
        print(drive_state)
        print(charge_state)
        time.sleep(60)

