import pandas as pd
from collections import defaultdict
import datetime
import sqlalchemy as sa

dt = datetime.datetime.now().date()


def transform_data(data):
    vehicle_data = defaultdict(list)
    for k, v in data.items():
        if type(v) in (int, str, bool, type(None)):
            vehicle_data['tesla'].append(pd.DataFrame.from_dict([{k: v}]))
            vehicle_data['tesla'].append(pd.DataFrame.from_dict([{'date': dt}]))
        elif type(v) == list:
            # print(k, v)
            for i, vv in enumerate(v):
                print(f'{k}_{i}: {vv}')
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


def import_data(dfs):

    engine = sa.create_engine('sqlite:///tesla.db')
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
                print(f'Data already imported for {dt}. Refreshing...')
                d = table_name.delete().where(table_name.c.date == dt)
                # print(d)
                res = d.execute()
                print(res.rowcount)
            missing_cols = [c for c in df.columns if c not in table_name.columns]
            if len(missing_cols) > 0:
                for i, col in enumerate(missing_cols):
                    print(table_name, f'{col}_{i}')
            print(f'Insert into table {table_name}')
            df.to_sql(table_name.name, engine, index=False, if_exists='append')
        else:
            raise Exception(f'Table {table_name} does not exist')
    print('Done')