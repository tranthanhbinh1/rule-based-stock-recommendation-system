import pandas as pd
from sqlalchemy import create_engine
from config.default import TS_DATABASE, TS_HOST, TS_PORT, TS_USERNAME, TS_PASSWORD
from dataclasses import dataclass


@dataclass
class TimescaleConnector():
    conn_str = f"postgresql://{TS_USERNAME}:{TS_PASSWORD}@{TS_HOST}:{TS_PORT}/{TS_DATABASE}"
    connector = create_engine(conn_str)
    
    @classmethod
    def insert(cls, df: pd.DataFrame, schema: str, table_name: str) -> None:
        df.to_sql(name=table_name, schema=schema, con=cls.conn_str, if_exists="append", index=False)  
    
    @classmethod
    def query_ohlcv_daily(cls):
        pass