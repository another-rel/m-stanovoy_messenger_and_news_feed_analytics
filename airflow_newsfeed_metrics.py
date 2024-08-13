import telegram
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import io
import pandas as pd
import pandahouse as ph

from datetime import datetime, timedelta
from airflow.decorators import dag, task
from airflow.operators.python import get_current_context

# Задаем параметры подключения к базе ClickHouse
connection = {
    'host': 'https://clickhouse.lab.karpov.courses',
    'password': 'dpo_python_2020',
    'user': 'student',
    'database': 'simulator_20240620'
}

# Устанавливаем параметры по умолчанию для DAG
default_args = {
    'owner': 'm-stanovoj',
    'depends_on_past': False,
    'retries': 2,
    'retry_interval': timedelta(minutes=5),
    'start_date': datetime(2024, 7, 18),
}

# Задаем график запуска DAG
schedule_interval = '0 11 * * *'

@dag(default_args=default_args, schedule_interval=schedule_interval, catchup=False)
def alerts_m_stanovoj_task_1():
    # chat_id = chat or 484715721 # устанавливаем айди чата
    chat_id = -938659451
    
    my_token = '6345792489:AAGDGiAHJZGu089Yir1DC4882zYkh5BxfJo' # сохраняем токен бота
    bot = telegram.Bot(token=my_token) # получаем доступ
    
    # Выгружаем агрегированные данные за вчера
    @task()
    def extract_yesterdays_data():
        feed_actions_yesterday = '''
                    select  yesterday() as observation_date,
                            today() as report_date,
                            count(distinct user_id) as DAU,
                            sum(action = 'like') as likes,
                            sum(action = 'view') as views,
                            round(sum(action = 'like') / sum(action = 'view'), 2) as CTR
                    from {db}.feed_actions
                    where toDate(time) = yesterday()
        '''
        yesterdays_data = ph.read_clickhouse(feed_actions_yesterday, connection=connection)
        return yesterdays_data
        
    # Выгружаем агрегированные данные за последнюю неделю
    @task()
    def extract_last_week_data():
        feed_actions_last_week = '''
                    select  toStartOfDay(time) as observation_date,
                            count(distinct user_id) as DAU,
                            sum(action = 'like') as likes,
                            sum(action = 'view') as views,
                            round(sum(action = 'like') / sum(action = 'view'), 3) as CTR
                    from {db}.feed_actions
                    where toStartOfDay(time) between (yesterday() - 6) and yesterday()
                    group by observation_date
        '''
        last_week_data = ph.read_clickhouse(feed_actions_last_week, connection=connection)
        return last_week_data
        
    # Создаем и отправляем текстовую часть отчета
    @task()
    def push_message(yesterdays_data, last_week_data):
        
        # Соберем нужные даты
        report_date = yesterdays_data['report_date'].iloc[0].strftime('%d/%m/%Y')
        observation_date = yesterdays_data['observation_date'].iloc[0].strftime('%d/%m/%Y')
        start_date = last_week_data['observation_date'].min().strftime('%d/%m/%Y')
        end_date = last_week_data['observation_date'].max().strftime('%d/%m/%Y')
        
        # Соберем данные по метрикам за вчера
        DAU = yesterdays_data['DAU'].iloc[0]
        likes = yesterdays_data['likes'].iloc[0]
        views = yesterdays_data['views'].iloc[0]
        CTR = yesterdays_data['CTR'].iloc[0]
        
        # Cформируем текстовую часть отчета
        msg = f'''Отчет от {report_date}
------------------------------------------------------------------------------------------
Ключевые метрики за {observation_date}:

DAU - {DAU}
Лайки - {likes}
Просмотры - {views}
CTR - {CTR}
------------------------------------------------------------------------------------------
Метрики в динамике за период {start_date} - {end_date}:
'''
        
        # Отправим сообщение в чат
        bot.sendMessage(chat_id=chat_id, text=msg)
     
    # Сформируем и отправим графики метрик за последнюю неделю
    @task()
    def push_plot(yesterdays_data, last_week_data):
        
        # Соберем нужные даты
        report_date = yesterdays_data['report_date'].iloc[0].strftime('%d/%m/%Y')
        start_date = last_week_data['observation_date'].min().strftime('%d/%m/%Y')
        end_date = last_week_data['observation_date'].max().strftime('%d/%m/%Y')
        
        # Подготовим сетку для графиков
        sns.set_theme()
        fig, axs = plt.subplots(ncols=2, nrows=2, figsize=(11.7, 8.27))

        # Отрисуем графики и определим их на слоты сетки
        likes_plot = sns.lineplot(ax=axs[0, 0],
                data=last_week_data,
                x='observation_date',
                y='likes',
                )

        views_plot = sns.lineplot(ax=axs[0, 1],
                data=last_week_data,
                x='observation_date',
                y='views',
                )

        CTR_plot = sns.lineplot(ax=axs[1, 0],
                data=last_week_data,
                x='observation_date',
                y='CTR',
                )

        DAU_plot = sns.lineplot(ax=axs[1, 1],
                data=last_week_data,
                x='observation_date',
                y='DAU',
                )

        # Стилизуем графики для лучшего визуального восприятия
        plt.setp(likes_plot.get_xticklabels(), rotation=45)
        plt.setp(views_plot.get_xticklabels(), rotation=45)
        plt.setp(CTR_plot.get_xticklabels(), rotation=45)
        plt.setp(DAU_plot.get_xticklabels(), rotation=45)
        
        likes_plot.set(xlabel='', ylabel='Лайки')
        views_plot.set(xlabel='', ylabel='Просмотры')
        CTR_plot.set(xlabel='', ylabel='CTR')
        DAU_plot.set(xlabel='', ylabel='DAU')

        # Настроим отступы и установим название
        fig.tight_layout()
        fig.subplots_adjust(top=.925)
        fig.suptitle(f'Метрики в динамике за период {start_date} - {end_date}')

        # Передадим полученный график в телеграм
        plot_object = io.BytesIO()
        plt.savefig(plot_object)
        plot_object.seek(0)
        plot_object.name = f'Отчет от {report_date}.png'
        plt.close()
        bot.sendPhoto(chat_id=chat_id, photo=plot_object)
        
    yesterdays_data = extract_yesterdays_data()
    last_week_data = extract_last_week_data()
    push_message(yesterdays_data, last_week_data)
    push_plot(yesterdays_data, last_week_data)
    
alerts_m_stanovoj_task_1 = alerts_m_stanovoj_task_1()