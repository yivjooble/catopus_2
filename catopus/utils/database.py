import psycopg2

from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool


def create_db_psycopg2_connection(host, dbname, user, password):
    return psycopg2.connect(
        f"host={host} dbname={dbname} user={user} password={password}")


def create_db_sqlalchemy_engine(host, dbname, user, password):
    return create_engine(
        f"postgresql+psycopg2://{user}:{password}@{host}/{dbname}",
        poolclass=QueuePool,
        pool_size=5,
        max_overflow=10)
