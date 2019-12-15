import pandas as pd
from collections import defaultdict
import datetime
import sqlalchemy as sa
import logging

dt = datetime.datetime.now().date()

logger = logging.getLogger('tesla-stats')


def transform_data(data):
    vehicle_data = defaultdict(list)
    for k, v in data.items():
        if type(v) in (int, str, bool, type(None)):
            vehicle_data['tesla'].append(pd.DataFrame.from_dict([{k: v}]))
            vehicle_data['tesla'].append(pd.DataFrame.from_dict([{'date': dt}]))
        elif type(v) == list:
            # print(k, v)
            for i, vv in enumerate(v):
                vehicle_data['tesla'].append(pd.DataFrame.from_dict([{f'{k}_{i}': vv}]))
        elif type(v) == dict:
            for kk, vv in v.items():
                if type(vv) == dict:
                    for kkk, vvv in vv.items():
                        vehicle_data[k].append(pd.DataFrame.from_dict([{f'{kk}_{kkk}': vvv}]))
                else:
                    vehicle_data[k].append(pd.DataFrame.from_dict([{kk: vv}]))
            vehicle_data[k].append(pd.DataFrame.from_dict([{'date': dt}]))

    dfs = dict()
    for k, v in vehicle_data.items():
        dfs[k] = pd.concat(v, axis=1)
    return dfs


def import_data(dfs, db):

    engine = sa.create_engine(f'sqlite:///{db["host"]}')
    metadata = sa.MetaData(engine)
    metadata.reflect()

    for table_name, df in dfs.items():
        if table_name in metadata.tables:
            table_name = metadata.tables[table_name]
            cnt_dt = sa.func.count('*').label('cnt')
            s = sa.select([cnt_dt], table_name.c.date == dt)
            # print(s)
            cnt = s.execute().scalar()
            if cnt == 1:
                logger.info(f'Data already imported for {dt}. Refreshing...')
                d = table_name.delete().where(table_name.c.date == dt)
                # print(d)
                res = d.execute()
                logger.info(f'{res.rowcount} rows deleted.')
            missing_cols = [c for c in df.columns if c not in table_name.columns]
            if len(missing_cols) > 0:
                logger.info('missing columns detected:')
                for i, col in enumerate(missing_cols):
                    logger.info(f'table: {table_name}, name: {col}, type: {df[col].dtype}')
                    if df[col].dtype == object:
                        type_ = 'TEXT'
                    elif df[col].dtype == pd.np.int:
                        type_ = 'BIGINT'
                    elif df[col].dtype == pd.np.float:
                        type_ = 'FLOAT'
                    else:
                        type_ = 'TEXT'
                    sql = f'''ALTER TABLE {table_name} ADD COLUMN {col} {type_}'''
                    logger.info(f'Sql: {sql}')
                    engine.execute(sql)
                    logger.info(f'Added column {col} to table {table_name}')
            logger.info(f'Insert into table {table_name}')
            df.to_sql(table_name.name, engine, index=False, if_exists='append')
        else:
            raise Exception(f'Table {table_name} does not exist')
    logger.info('Done')