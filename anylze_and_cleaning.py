from datetime import datetime


def date_to_number(date):
    date = date.split(',')
    if(len(date) < 3):
        return None
    date[1] = date[1].split(' ')
    try:
        return mounth_to_num[date[1][1]].zfill(2) + date[1][2].zfill(2) + date[2].strip()
    except:
        return None


def time_from_start(date):
    date = date_to_number(date)
    date_time = datetime(year=int(date[4:8]), month=int(
        date[0:2]), day=int(date[2:4]))
    if date_time.month >= 9:
        start = datetime(year=int(date[4:8]), month=9, day=1)
    else:
        start = datetime(year=int(date[4:8])-1, month=9, day=1)
    return (date_time-start).days


def date_to_seasons(date):
    date = date_to_number(date)
    date_time = datetime(year=int(date[4:8]), month=int(
        date[0:2]), day=int(date[2:4]))
    if date_time.month >= 9:
        season = date_time.year + 1
    else:
        season = date_time.year
    return season


mounth_to_num = {
    "Jan": '1',
    "Feb": '2',
    "Mar": '3',
    "Apr": '4',
    "May": '5',
    "Jun": '6',
    "Jul": '7',
    "Aug": '8',
    "Sep": '9',
    "Oct": '10',
    "Nov": '11',
    "Dec": '12'
}


def date_to_season_and_days(game):
    game['days_from_start'] = time_from_start(game['date'])
    game['Season'] = date_to_seasons(game['date'])
    if game['days_from_start'] is None:
        raise ValueError("That is currect date")
    del game['date']
