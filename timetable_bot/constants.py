import datetime

default_table_periods = [
    (datetime.time(8, 20), datetime.time(9, 50)),
    (datetime.time(10, 0), datetime.time(11, 30)),
    (datetime.time(11, 40), datetime.time(13, 10)),
    (datetime.time(13, 30), datetime.time(15, 0)),
    (datetime.time(15, 20), datetime.time(16, 50)),
    (datetime.time(17, 0), datetime.time(18, 30)),
    (datetime.time(18, 40), datetime.time(20, 10)),
]

days_of_week = [
    "Понедельник",
    "Вторник",
    "Среда",
    "Четверг",
    "Пятница",
    "Суббота",
    "Воскресенье",
]

TZ_UTC_OFFSET = datetime.timedelta(hours=3)
