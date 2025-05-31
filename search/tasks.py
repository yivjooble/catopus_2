import logging
import os
import pandas as pd

from django.utils import timezone

from celery import shared_task
from multiprocessing import Process
from multiprocessing import Queue, Manager

from datetime import datetime
from dotenv import load_dotenv

# custom modules
from .config import connection_info, map_country_code_to_id as code_to_id
from catopus.utils.database import create_db_sqlalchemy_engine
from sqlalchemy import text

logger = logging.getLogger('search')

load_dotenv()



def exec_sql_remote(query, results_list):
    try:
        get_query = query.get()

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

        results_list.append(final_df)
    except Exception as e:
        logger.error(f"exec_sql_remote: {e}")


@shared_task
def run_sql_query_remotely(rmt_user, rmt_input_code, rmt_countries, rmt_countries_list=None):
    from .models import RemoteLogs

    try:
        # Change status of run query to "running" and save info to dwh
        log_remote = RemoteLogs(user=rmt_user,
                                status="start",
                                sql_query=rmt_input_code,
                                countries_list=rmt_countries_list,
                                countries=rmt_countries)
        log_remote.save()

        # Run sql query over all selected countries
        processes = []
        result = Manager()
        results_list = result.list() # stores all dfs

        for cluster, cluster_conn_info in connection_info.items():
            for db_name in cluster_conn_info['dbs']:
                if db_name in rmt_countries:

                    query = Queue()
                    info = {"host": cluster_conn_info['host'],
                            "port": cluster_conn_info['port'],
                            "db_name": db_name,
                            "code": rmt_input_code}
                    query.put(info)

                    process = Process(target=exec_sql_remote, args=(query, results_list, ))
                    processes.append(process)

        # start all processes
        for process in processes:
            process.start()

        for process in processes:
            process.join()

        if len(results_list) == 0:
            # If empty result, update system table with appropriate info
            log_remote.status = "empty"
            log_remote.updated_on = timezone.now()
            log_remote.save()
        else:
            res_df = pd.concat(results_list, ignore_index=True)
            table_name = str(rmt_user) + '_rmt_' + timezone.now().strftime("%Y%m%d_%H_%M_%S")

            res_df.to_sql(
                table_name,
                con=create_db_sqlalchemy_engine(
                    os.environ.get('DWH_HOST'),
                    os.environ.get('DWH_DB'),
                    os.environ.get('DWH_USER'),
                    os.environ.get('DWH_PASSWORD')),
                schema='catopus',
                index=False,
                chunksize=10000)

            log_remote.status = "finished"
            log_remote.table_name_created = table_name
            log_remote.updated_on = timezone.now()
            log_remote.save()

    except Exception as e:
        # Insert error into dwh cat_remote_run table
        logger.error(f"run_sql_query_remotely: {e}")
        log_remote.status = "error"
        log_remote.log_field = e
        log_remote.updated_on = timezone.now()
        log_remote.save()