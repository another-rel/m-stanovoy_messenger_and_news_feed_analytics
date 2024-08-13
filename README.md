# Описание проекта

## Цель проекта: Создание базового аналитического контура для оценки эффективности работы мобильного приложения и последующее исследование данных

Работа выполнена на **Python** с использованием **Jupyter Notebook**. Запросы к базам данных **ClickHouse** осуществлялись посредством библиотеки **pandahouse**.

### **Задача 1** 

Создать аналитический контур мобильного приложения, а именно:
- Разработать аналитический дашборд для оценки работы ленты новостей
- Разработать оперативный дашборд для оценки работы ленты новостей
- Разработать аналитический дашборд для оценки совместной работы мессенджера и ленты новостей

Скриншоты выполненных задач в Apache Superset:
- Аналитический дашборд для оценки работы ленты новостей
<div align="center">
  <img src="https://github.com/another-rel/m-stanovoy_messenger_and_news_feed_analytics/blob/f015d8bc8d9efb819e483bd3c5b2779b94f5c53f/assets/superset_newsfeed_analytical_dashboard.png"/>
</div>
<br>

- Оперативный дашборд для оценки работы ленты новостей
<div align="center">
  <img src="https://github.com/another-rel/m-stanovoy_messenger_and_news_feed_analytics/blob/f015d8bc8d9efb819e483bd3c5b2779b94f5c53f/assets/superset_newsfeed_operational_dashboard.png"/>
</div>
<br>

- Аналитический дашборд для оценки работы ленты новостей
<div align="center">
  <img src="https://github.com/another-rel/m-stanovoy_messenger_and_news_feed_analytics/blob/f015d8bc8d9efb819e483bd3c5b2779b94f5c53f/assets/superset_full_app_analytical_dashboard.png"/>
</div>

### **Задача 2**

Провести анализ продуктовых метрик приложения:
- Проанализировать и сравнить *retention* по типу каналов привлечения (платный трафик source = 'ads', и органические каналы source = 'organic')
- Проанализировать качество трафика, полученного в результате маркетинговой компании 13 июня 2024 года
- Проанализировать трафик 22 июня 2024 года и определить причины резкого падения дневной аудитории
- Визуализировать недельную аудиторию по типам пользователей (новые, старые, ушедшие)

Скриншот аналитического отчета в Apache Superset:

<div align="center">
  <img src="https://github.com/another-rel/m-stanovoy_messenger_and_news_feed_analytics/blob/f015d8bc8d9efb819e483bd3c5b2779b94f5c53f/assets/superset_product_analysis_report.png"/>
</div>

### **Задача 3**

Оценить корректность работы системы сплитования по проведенному А/А-тесту.

### **Задача 4**

Провести анализ данных А/B-теста по внедрению новых алгоритмов рекомендации постов в ленте новостей.

### **Задача 5**

Построить ETL-пайплайн для выгрузки данных из ClickHouse, расчета продуктовых метрик по срезам (os, gender, age) и последующему аккумулированию результов в новой таблице.

### **Задача 6**

Автоматизировать ежедневную отчетность по ключевым метрикам продукта, а именно:
- Настроить отправку отчета по ключевым метрикам **ленты новостей** за вчера + графики метрик в динамике за прошедшую неделю в общий чат Telegram
- Настроить отправку отчета по ключевым метрикам **всего продукта** за вчера + графики метрик в динамике за прошедшую неделю в общий чат Telegram

Скриншоты примеров готовых отчетов в Telegram:
- Пример готового отчета по ключевым метрикам **ленты новостей** в Telegram
<div align="center">
  <img src="https://github.com/another-rel/m-stanovoy_messenger_and_news_feed_analytics/blob/f015d8bc8d9efb819e483bd3c5b2779b94f5c53f/assets/airflow_newsfeed_metrics_chat.png"/>
</div>
<br>

- График отчета по ключевым метрикам **ленты новостей**
<div align="center">
  <img src="https://github.com/another-rel/m-stanovoy_messenger_and_news_feed_analytics/blob/5ae3a3be68b0d7998f842a49171a2569a278037f/assets/airflow_newsfeed_metrics_graph.png"/>
</div>
<br>

- Пример готового отчета по ключевым метрикам **всего продукта** в Telegram
<div align="center">
  <img src="https://github.com/another-rel/m-stanovoy_messenger_and_news_feed_analytics/blob/f015d8bc8d9efb819e483bd3c5b2779b94f5c53f/assets/airflow_full_app_metrics_chat.png"/>
</div>
<br>

- График отчета по ключевым метрикам **всего продукта**
<div align="center">
  <img src="https://github.com/another-rel/m-stanovoy_messenger_and_news_feed_analytics/blob/17724611c7e3a63a7d1e7934b12e16a1d85b5e51/assets/airflow_full_app_metrics_graph.png"/>
</div>
<br>

<hr>

### **Реализация проекта:**
<ul>
<li>Создан аналитический контур мобильного приложения, позволяющий отслеживать состояние приложения за длительный и кратковременный периоды.</li>
<li>Проведен анализ продуктовых метрик приложения и оформлен в Apache Superset.</li>
<li>Проведена оценка корректности работы системы сплитования по проведенному А/А-тесту.</li>
<li>Проведен анализ данных А/B-теста по внедрению новых алгоритмов рекомендации постов в ленте новостей с использованием статистических тестов в Python (пуассоновский бутстрап, T-test).</li>
<li>Построен ETL-пайплайн для расчета продуктовых метрик приложения по срезам (os, gender, age).</li>
<li>Автоматизирована ежедневная отчетность по ключевым метрикам продукта.</li>
</ul>
