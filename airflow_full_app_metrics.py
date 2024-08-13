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
def alerts_m_stanovoj_task_2():
    # chat_id = chat or 484715721 # устанавливаем айди чата
    chat_id = -938659451
    
    my_token = '6345792489:AAGDGiAHJZGu089Yir1DC4882zYkh5BxfJo' # сохраняем токен бота
    bot = telegram.Bot(token=my_token) # получаем доступ
    
    # Выгружаем агрегированные данные за вчера
    @task()
    def extract_feed_yesterdays_data():
        feed_actions_yesterday = '''
            select  yesterday() as observation_date,
                                today() as report_date,
                                sum(action = 'like') as likes,
                                round((sum(action = 'like') - (select sum(action = 'like') from {db}.feed_actions where toDate(time) = yesterday() - 1)) / (select sum(action = 'like') from {db}.feed_actions where toDate(time) = yesterday() - 1) * 100, 1) as likes_diff,
                                sum(action = 'view') as views,
                                round((sum(action = 'view') - (select sum(action = 'view') from {db}.feed_actions where toDate(time) = yesterday() - 1)) / (select sum(action = 'view') from {db}.feed_actions where toDate(time) = yesterday() - 1) * 100, 1) as views_diff,
                                count(distinct post_id) as unique_posts,
                                round((count(distinct post_id) - (select count(distinct post_id) from {db}.feed_actions where toDate(time) = yesterday() - 1)) / (select count(distinct post_id) from {db}.feed_actions where toDate(time) = yesterday() - 1) * 100, 1) as post_diff
                        from {db}.feed_actions
                        where toDate(time) = yesterday()
        '''
        feed_yesterdays_data = ph.read_clickhouse(feed_actions_yesterday, connection=connection)
        return feed_yesterdays_data
    
    @task()
    def extract_message_yesterdays_data():
        message_actions_yesterday = '''
            select  yesterday() as observation_date,
                    today() as report_date,
                    count(distinct user_id) as messages_sent,
                    round((count(distinct user_id) - (select count(distinct user_id) from {db}.message_actions where toDate(time) = yesterday() - 1)) / (select count(distinct user_id) from {db}.message_actions where toDate(time) = yesterday() - 1) * 100, 1) as messages_diff
            from {db}.message_actions
            where toDate(time) = yesterday()
        '''
        message_yesterdays_data = ph.read_clickhouse(message_actions_yesterday, connection=connection)
        return message_yesterdays_data
    
    @task()
    def extract_combined_yesterdays_data():
        combined_yesterday = '''
            select yesterday() as observation_date,
                   today() as report_date,
                   count(distinct user_id) FILTER (where toDate(time) = yesterday()) as DAU,
                   round((count(distinct user_id) FILTER (where toDate(time) = yesterday()) - 
                   count(distinct user_id) FILTER (where toDate(time) = yesterday() - 1)) /
                   count(distinct user_id) FILTER (where toDate(time) = yesterday() - 1) * 100, 1) as DAU_diff
            from
                    (select toStartOfDay(time) as time,
                        user_id
                    from {db}.feed_actions as n
                    join (select user_id from {db}.message_actions) as m
                    on n.user_id = m.user_id
                    where toDate(time) between yesterday() - 1 and yesterday())
        '''
        combined_yesterdays_data = ph.read_clickhouse(combined_yesterday, connection=connection)
        return combined_yesterdays_data
        
    # Выгружаем агрегированные данные за последнюю неделю
    @task()
    def extract_feed_last_week_data():
        feed_actions_last_week = '''
            select  toStartOfDay(time) as observation_date,
                    sum(action = 'like') as likes,
                    sum(action = 'view') as views,
                    count(distinct post_id) as unique_posts
            from {db}.feed_actions
            where toDate(time) between (yesterday() - 6) and yesterday()
            group by observation_date
        '''
        feed_last_week_data = ph.read_clickhouse(feed_actions_last_week, connection=connection)
        return feed_last_week_data
    
    @task()
    def extract_message_last_week_data():
        message_actions_last_week = '''
            select  toStartOfDay(time) as observation_date,
                    count(distinct user_id) as messages_sent
            from {db}.message_actions
            where toDate(time) between (yesterday() - 6) and yesterday()
            group by observation_date
        '''
        message_last_week_data = ph.read_clickhouse(message_actions_last_week, connection=connection)
        return message_last_week_data
    
    @task()
    def extract_combined_last_week_data():
        combined_last_week = '''
            select toStartOfDay(time) as observation_date,
                   count(distinct user_id) as DAU
            from
                    (select time,
                        user_id
                    from {db}.feed_actions as n
                    join (select user_id from {db}.message_actions) as m
                    on n.user_id = m.user_id
                    where toDate(time) between (yesterday() - 6) and yesterday())
            group by observation_date
        '''
        combined_last_week_data = ph.read_clickhouse(combined_last_week, connection=connection)
        return combined_last_week_data
        
    # Создаем и отправляем текстовую часть отчета
    @task()
    def push_message(feed_yesterdays_data, message_yesterdays_data, combined_yesterdays_data, feed_last_week_data):
        
        # Соберем нужные даты
        report_date = feed_yesterdays_data['report_date'].iloc[0].strftime('%d/%m/%Y')
        observation_date = feed_yesterdays_data['observation_date'].iloc[0].strftime('%d/%m/%Y')
        start_date = feed_last_week_data['observation_date'].min().strftime('%d/%m/%Y')
        end_date = feed_last_week_data['observation_date'].max().strftime('%d/%m/%Y')
        
        # Соберем данные по метрикам за вчера по ленте новостей
        likes = feed_yesterdays_data['likes'].iloc[0]
        likes_diff = feed_yesterdays_data['likes_diff'].iloc[0]
        views = feed_yesterdays_data['views'].iloc[0]
        views_diff = feed_yesterdays_data['views_diff'].iloc[0]
        posts = feed_yesterdays_data['unique_posts'].iloc[0]
        post_diff = feed_yesterdays_data['post_diff'].iloc[0]
        
        # Соберем данные по метрикам за вчера по мессенджеру
        messages_sent = message_yesterdays_data['messages_sent'].iloc[0]
        messages_diff = message_yesterdays_data['messages_diff'].iloc[0]
        
        # Соберем данные по метрикам за вчера по комбинированным данным
        DAU = combined_yesterdays_data['DAU'].iloc[0]
        DAU_diff = combined_yesterdays_data['DAU_diff'].iloc[0]
        
        # Cформируем текстовую часть отчета
        msg = f'''Отчет от {report_date}
------------------------------------------------------------------------------------------
Ключевые метрики за {observation_date}:

Лента новостей:
Лайки - {likes} ({likes_diff}% за день)
Просмотры - {views} ({views_diff}% за день)
Уникальные посты - {posts} ({post_diff}% за день)

Мессенджер:
Сообщений отправлено - {messages_sent} ({messages_diff}% за день)

Общее:
DAU - {DAU} ({DAU_diff}% за день)
------------------------------------------------------------------------------------------
Метрики в динамике за период {start_date} - {end_date}:
'''
        
        # Отправим сообщение в чат
        bot.sendMessage(chat_id=chat_id, text=msg)
     
    # Сформируем и отправим графики метрик за последнюю неделю
    @task()
    def push_plot(feed_yesterdays_data, feed_last_week_data, message_last_week_data, combined_last_week_data):
        
        # Соберем нужные даты
        report_date = feed_yesterdays_data['report_date'].iloc[0].strftime('%d/%m/%Y')
        start_date = feed_last_week_data['observation_date'].min().strftime('%d/%m/%Y')
        end_date = feed_last_week_data['observation_date'].max().strftime('%d/%m/%Y')
        
        # Подготовим сетку для графиков
        sns.set_theme()
        fig, axs = plt.subplots(nrows=5, figsize=(8.27, 23.4))

        # Отрисуем графики и определим их на слоты сетки
        likes_plot = sns.lineplot(ax=axs[0],
                data=feed_last_week_data,
                x='observation_date',
                y='likes',
                )

        views_plot = sns.lineplot(ax=axs[1],
                data=feed_last_week_data,
                x='observation_date',
                y='views',
                )

        posts_plot = sns.lineplot(ax=axs[2],
                data=feed_last_week_data,
                x='observation_date',
                y='unique_posts',
                )
        
        messages_plot = sns.lineplot(ax=axs[3],
                data=message_last_week_data,
                x='observation_date',
                y='messages_sent',
                )

        DAU_plot = sns.lineplot(ax=axs[4],
                data=combined_last_week_data,
                x='observation_date',
                y='DAU',
                )

        # Стилизуем графики для лучшего визуального восприятия
        plt.setp(likes_plot.get_xticklabels(), rotation=45)
        plt.setp(views_plot.get_xticklabels(), rotation=45)
        plt.setp(posts_plot.get_xticklabels(), rotation=45)
        plt.setp(messages_plot.get_xticklabels(), rotation=45)
        plt.setp(DAU_plot.get_xticklabels(), rotation=45)
        
        likes_plot.set(xlabel='', ylabel='Лайки')
        views_plot.set(xlabel='', ylabel='Просмотры')
        posts_plot.set(xlabel='', ylabel='Уникальные посты')
        messages_plot.set(xlabel='', ylabel='Отправлено сообщений')
        DAU_plot.set(xlabel='', ylabel='Общий DAU')

        # Настроим отступы и установим название
        fig.tight_layout()
        fig.subplots_adjust(top=.95)
        fig.suptitle(f'Метрики в динамике за период {start_date} - {end_date}')

        # Передадим полученный график в телеграм
        plot_object = io.BytesIO()
        plt.savefig(plot_object)
        plot_object.seek(0)
        plot_object.name = f'Отчет от {report_date}.png'
        plt.close()
        bot.sendPhoto(chat_id=chat_id, photo=plot_object)
        
    feed_yesterdays_data = extract_feed_yesterdays_data()
    message_yesterdays_data = extract_message_yesterdays_data()
    combined_yesterdays_data = extract_combined_yesterdays_data()
    
    feed_last_week_data = extract_feed_last_week_data()
    message_last_week_data = extract_message_last_week_data()
    combined_last_week_data = extract_combined_last_week_data()
    
    push_message(feed_yesterdays_data, message_yesterdays_data, combined_yesterdays_data, feed_last_week_data)
    push_plot(feed_yesterdays_data, feed_last_week_data, message_last_week_data, combined_last_week_data)
    
alerts_m_stanovoj_task_2 = alerts_m_stanovoj_task_2()