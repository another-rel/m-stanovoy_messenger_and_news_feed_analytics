from datetime import datetime, timedelta
import pandas as pd
import pandahouse as ph
import numpy as np

from airflow.decorators import dag, task
from airflow.operators.python import get_current_context

# Устанавливаем параметры по умолчанию для DAG
default_args = {
    'owner': 'm-stanovoj',
    'depends_on_past': False,
    'retries': 2,
    'retry_interval': timedelta(minutes=5),
    'start_date': datetime(2024, 1, 1),
}

# Задаем график запуска DAG
schedule_interval = '0 7 * * *'

# Задаем параметры подключения к базе ClickHouse
connection = {
    'host': 'https://clickhouse.lab.karpov.courses',
    'password': 'dpo_python_2020',
    'user': 'student',
    'database': 'simulator_20240620'
}

@dag(default_args=default_args, schedule_interval=schedule_interval, catchup=False)
def dag_m_stanovoj():

    # Выгружаем данные кол-ва лайков и просмотров на пользователя
    @task()
    def extract_feed_actions():
        feed_actions_query = '''
            select  yesterday() as event_date,
                    user_id,
                    sum(action = 'like') as likes,
                    sum(action = 'view') as views,
                    max(gender) as gender,
                    max(age) as age,
                    max(os) as os
            from {db}.feed_actions
            where toDate(time) = yesterday()
            group by user_id
        '''
        feed_actions_data = ph.read_clickhouse(feed_actions_query, connection=connection)
        return feed_actions_data
    
    # Выгружаем данные сообщений на пользователя
    @task()
    def extract_message_actions():
        message_actions_query = '''
            select  yesterday() as event_date,
                    user_id,
                    count(receiver_id) as messages_sent,
                    countIf(user_id in  (select receiver_id from {db}.message_actions
                    where toDate(time) = yesterday())
                    ) as messages_received,
                    count(distinct receiver_id) as users_sent,
                    countIf(user_id in  (select distinct receiver_id from {db}.message_actions
                    where toDate(time) = yesterday())
                    ) as users_received,
                    max(gender) as gender,
                    max(age) as age,
                    max(os) as os
            from {db}.message_actions
            where toDate(time) = yesterday()
            group by user_id
        '''
        message_actions_data = ph.read_clickhouse(message_actions_query, connection=connection)
        return message_actions_data    

    # Объединяем таблицы
    @task
    def merge(feed_actions_data, message_actions_data):
        merged_data = feed_actions_data.merge(message_actions_data, on=['event_date', 'user_id', 'gender', 'age', 'os'], how='outer').fillna(0)
        return merged_data
    
    # Рассчитаем срез по операционной системе
    @task
    def calculate_by_os(merged_data):
        os_dimension = merged_data.groupby(['event_date', 'os'])\
            .agg(views=('views', 'sum'),
                 likes=('likes', 'sum'),
                 messages_received=('messages_received', 'sum'),
                 messages_sent=('messages_sent', 'sum'),
                 users_received=('users_received', 'sum'),
                 users_sent=('users_sent', 'sum')
                )\
            .reset_index()\
            .rename(columns={'os': 'dimension_value'})
        os_dimension.dimension_value = os_dimension.dimension_value.astype(str)
        os_dimension.insert(loc=1, column='dimension', value='os')
        return os_dimension

    # Рассчитаем срез по полу
    @task
    def calculate_by_gender(merged_data):
        gender_dimension = merged_data.groupby(['event_date', 'gender'])\
            .agg(views=('views', 'sum'),
                 likes=('likes', 'sum'),
                 messages_received=('messages_received', 'sum'),
                 messages_sent=('messages_sent', 'sum'),
                 users_received=('users_received', 'sum'),
                 users_sent=('users_sent', 'sum')
                )\
            .reset_index()\
            .rename(columns={'gender': 'dimension_value'})
        gender_dimension.dimension_value = gender_dimension.dimension_value.astype(str)
        gender_dimension.insert(loc=1, column='dimension', value='gender')
        return gender_dimension
    
    # Рассчитаем срез по возрасту
    @task
    def calculate_by_age(merged_data):
        age_dimension = merged_data.groupby(['event_date', 'age'])\
            .agg(views=('views', 'sum'),
                 likes=('likes', 'sum'),
                 messages_received=('messages_received', 'sum'),
                 messages_sent=('messages_sent', 'sum'),
                 users_received=('users_received', 'sum'),
                 users_sent=('users_sent', 'sum')
                )\
            .reset_index()\
            .rename(columns={'age': 'dimension_value'})
        age_dimension.dimension_value = age_dimension.dimension_value.astype(str)
        age_dimension.insert(loc=1, column='dimension', value='age')
        return age_dimension

    # Осуществим загрузку данных в таблицу тестовой базы Clickhouse
    @task
    def load_to_clickhouse(os_dimension, gender_dimension, age_dimension):
        combined_data = pd.concat([os_dimension, gender_dimension, age_dimension])
        combined_data[['views', 'likes', 'messages_sent', 'users_sent', 'messages_received', 'users_received']] = combined_data[['views', 'likes', 'messages_sent', 'users_sent', 'messages_received', 'users_received']].astype(np.int64)
        connection_test = {
            'host': 'https://clickhouse.lab.karpov.courses',
            'database': 'test',
            'user': 'student-rw',
            'password': '656e2b0c9c'
        }
        ph.to_clickhouse(df=combined_data, table='dag_m_stanovoj_practice_da', index=False, connection=connection_test)

    # Запускаем DAG
    feed_actions_data = extract_feed_actions()
    message_actions_data = extract_message_actions()
    merged_data = merge(feed_actions_data, message_actions_data)
    os_dimension = calculate_by_os(merged_data)
    gender_dimension = calculate_by_gender(merged_data)
    age_dimension = calculate_by_age(merged_data)
    
    load_to_clickhouse(os_dimension, gender_dimension, age_dimension)
    
dag_m_stanovoj = dag_m_stanovoj()