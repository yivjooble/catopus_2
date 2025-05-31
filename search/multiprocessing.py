import logging
import os
import pandas as pd

from multiprocessing import Process
from multiprocessing import Queue, Manager

from django.utils import timezone

from psycopg2 import errors as psycopg2_errors
from sqlalchemy import text
from dotenv import load_dotenv
from typing import Dict, List

from concurrent.futures import ThreadPoolExecutor, as_completed

# custom modules
from search.config import connection_info, map_country_code_to_id as code_to_id
from catopus.utils.database import create_db_sqlalchemy_engine

logger = logging.getLogger('search')

load_dotenv()



#  Read sql query from input field
def exec_sql_multiproc(info: Dict[str, str]):
    try:
        get_query = info

        df = pd.read_sql_query(sql=text(get_query['code']),
                               con=create_db_sqlalchemy_engine(get_query['host'],
                                                                get_query['db_name'],
                                                                os.environ.get('RPL_USER'),
                                                                os.environ.get('RPL_PASSWORD')))

        columns = list(df.columns)
        copy_df = df.copy()
        copy_df['_country_code'] = get_query['db_name']
        copy_df['_country_id'] = code_to_id[get_query['db_name']]
        final_df = copy_df[['_country_id', '_country_code', *columns]]

        return final_df
    except psycopg2_errors.UndefinedTable as e:  # Catch table not found error
        logger.warning(f"Table not found WARNING: {e}")
        return None  # Return None so that the main function can continue
    except psycopg2_errors.Error as e:  # Catch other psycopg2 errors
        logger.error(f"ERROR: {e}")
        return None  # Return None so that the main function can continue


#  Run sql query over all selected countries
def run_select(code: str, countries: List[str], customer_table_name : str=None) -> pd.DataFrame:
    try: 
        # processes = []
        # result = Manager()
        # results_list = result.list()
        results_list = []

        with ThreadPoolExecutor(8) as executor:
            futures = []
        
            for cluster, cluster_conn_info in connection_info.items():
                for db_name in cluster_conn_info['dbs']:
                    if db_name in countries:                    
                        info = {"host": cluster_conn_info['host'],
                                    "port": cluster_conn_info['port'],
                                    "db_name": db_name,
                                    "code": code}
                        future = executor.submit(exec_sql_multiproc, info)
                        futures.append(future)

            # start all processes
            for future in as_completed(futures):
                result = future.result()

                if result is not None:
                    results_list.append(result)

            # create a dataframe with result
            if len(results_list) == 0:
                return pd.DataFrame({
                    'result': 'None'
                })
            else:
                result_df = pd.concat(results_list, ignore_index=True)

                if customer_table_name:
                    logger.info(f"user provides custom table name to save into db: {customer_table_name}")
                    table_name = str(customer_table_name) + '_' + timezone.now().strftime("%Y%m%d_%H_%M_%S")

                    result_df.to_sql(
                        table_name,
                        con=create_db_sqlalchemy_engine(
                            os.environ.get('DWH_HOST'),
                            os.environ.get('DWH_DB'),
                            os.environ.get('DWH_USER'),
                            os.environ.get('DWH_PASSWORD')),
                        schema='catopus',
                        index=False,
                        chunksize=10000)
                    
                    return result_df, table_name
                else:
                    return result_df

    except Exception as e:
        logger.error(f"run_select ERROR: {e}")