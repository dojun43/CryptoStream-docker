from airflow import DAG
import pendulum
from datetime import datetime, timedelta
from sensors.gcs_orderbook_5m_sensor import GcsOrderbook5mSensor
from sensors.gcs_parquet_sensor import GcsParquetSensor
from operators.json_to_parquet_operator import JsonToParquetOperator
from operators.insert_ohlc_5m_table_operator import InsertOhlc5mTableOperator
from airflow.utils.trigger_rule import TriggerRule


with DAG(
    dag_id="dags_transform_orderbook3",
    schedule_interval=timedelta(minutes=5),
    start_date=pendulum.datetime(2025,2,14, tz='Asia/Seoul'),
    catchup=False,
) as dag:
    
    ticker_list = ["ICX","EOS","TRX","SC","ONT","ZIL","POLYX","ZRX","LOOM","BCH"]
    
    gcs_orderbook_5m_sensor_tasks = [
            GcsOrderbook5mSensor(
                task_id=f'gcs_orderbook_5m_sensor_{ticker}',
                ticker=ticker,
                poke_interval=10,
                timeout=120,
                mode='reschedule'
            ) 
            for ticker in ticker_list]
    
    json_to_parquet_tasks = [
            JsonToParquetOperator(
                task_id=f'json_to_parquet_{ticker}',
                trigger_rule=TriggerRule.ALL_SUCCESS,
                ticker=ticker,
                gcs_conn_id='conn-gcp-cryptostream'
            )
            for ticker in ticker_list]

    gcs_parquet_sensor_tasks = [
            GcsParquetSensor(
                task_id=f'gcs_parquet_sensor_{ticker}',
                json_to_parquet_task_id=f'json_to_parquet_{ticker}',
                poke_interval=5,
                timeout=5*6,
                mode='reschedule'
            ) 
            for ticker in ticker_list]

    insert_olhc_5m_table_tasks = [
            InsertOhlc5mTableOperator(
                task_id=f'insert_olhc_5m_table_{ticker}',
                trigger_rule=TriggerRule.ALL_SUCCESS,
                ticker=ticker, 
                gcs_conn_id='conn-gcp-cryptostream', 
                postgres_conn_id='conn-postgres', 
                json_to_parquet_task_id=f'json_to_parquet_{ticker}'
            ) 
            for ticker in ticker_list]

    for gcs_orderbook_5m_sensor, json_to_parque, gcs_parquet_sensor, insert_5minute_table in zip(gcs_orderbook_5m_sensor_tasks, json_to_parquet_tasks, gcs_parquet_sensor_tasks, insert_olhc_5m_table_tasks):
        gcs_orderbook_5m_sensor >> json_to_parque >> gcs_parquet_sensor >> insert_5minute_table
