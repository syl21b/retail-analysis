from airflow import DAG
from airflow.providers.microsoft.mssql.operators.mssql import MsSqlOperator
from datetime import datetime

default_args = {
    'start_date': datetime(2024, 1, 1)
}

with DAG(
    dag_id='retail_etl_pipeline',
    schedule_interval='@daily',
    catchup=False,
    default_args=default_args
) as dag:

    run_etl = MsSqlOperator(
        task_id='run_full_etl',
        mssql_conn_id='mssql_default',
        sql='EXEC sp_run_full_etl;'
    )