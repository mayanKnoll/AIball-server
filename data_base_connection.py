from sklearn import cluster
from typing import Dict, List
from pymongo import MongoClient
import pandas as pd
import sys
from datetime import date
from anylze_and_cleaning import time_from_start
# sys.path.insert(
#     0, r'..\AIball\Scrapper')
import scrapper

cluster = MongoClient(
    "mongodb+srv://Aiball:yuval1andmayan1@cluster0.fadet.mongodb.net/myFirstDatabase?retryWrites=true&w=majority")
db = cluster["AIball"]
balance = db["balance"]
played_games = db["played_games"]
next_games = db["next_games"]



def date_to_start(date):
    return (date - date(date.year - 1, 9,1)).days % 365


def get_teams() -> pd.DataFrame:
    pass


def create_balance():
    balance.delete_many({})
    today = date.today()
    teams = [x.split('\xa0')[0]
             for x in scrapper.get_teams_names(today.year).keys()]
    for team in teams:
        if today.month < 9:
            balance.insert_one({"team_name": team, "wins": 0, "losses": 0, "balance": 0, "games": 0,
                               "points": 0, "days_last": (today - date(today.year - 1, 9, 1)).days - 15})
        else:
            balance.insert_one({"team_name": team, "wins": 0, "losses": 0, "balance": 0, "games": 0,
                               "points": 0, "days_last": (today - date(today.year, 9, 1)).days - 15})



PLACE = {True: "home_group", False: "visitor_group"}
SHORT_PLACE = {True:  'Hm', False: "Vis"}
# {9 : date(year-1, 9, 30), 10 : date(year-1, 10, 31), 11 : date(year-1, 11, 30),
        # 12 : date(year - 1, 12, 31),1 : date(year, 1, 31),2 : date(year, 2, 28),
        # 3 : date(year, 3, 31),4 : date(year, 4, 30),5 : date(year, 5, 31), : date(year, 6, 30)}

def get_month(today):
    if today.month > 9:
        year = today.year - 1
    else:
        year = today.year
    return [date(year-1, 10, 31), date(year-1, 11, 30), date(year - 1, 12, 31), date(year, 1, 31),
          date(year, 2, 28), date(year, 3, 31), date(year, 4, 30), date(year, 5, 31), date(year, 6, 30)]


def get_last_games(last_game_date) -> List[List[str]]:
    game_list = list()
    for month in get_month(date.today()):

        if date.today() < month:
            break
        games = scrapper.get_games(month.year, month.strftime("%B"))
        if games is None:
            continue
        for game in games:
            if len(game) < 6 or game[3] is '':
                continue
            game_dict = {"date": time_from_start(game[0]), "home_group": game[4], "home_pts": int(game[5]),
                         "visitor_group": game[2], "vis_pts": int(game[3])}
            game_list.append(game_dict)
    return game_list



def update_balance(game_result):
    home_group = game_result['home_group']
    visitor_group = game_result['visitor_group']
    date = time_from_start(game_result['date'])
    points_result = game_result['home_pts'] - game_result['vis_pts']
    if points_result > 0:
        balance.update_one({"team_name": home_group}, {'$inc': {"balance": points_result,
        "games": 1, "points": game_result['home_pts'], "wins": 1}, "$set": {"date": date}})
        balance.update_one({"team_name": visitor_group}, {'$inc': {"balance": -points_result,
         "games": 1, "points": game_result['vis_pts'], "losses": 1}, "$set": {"date": date}})
    else:
        balance.update_one({"team_name": home_group}, {'$inc': {"balance": points_result,
         "games": 1, "points": game_result['home_pts'], "losses" : 1}, "$set": {"days_last": date}})
        balance.update_one({"team_name": visitor_group}, {'$inc': {"balance": -points_result,
         "games": 1, "points": game_result['vis_pts'], "wins" : 1}, "$set": {"days_last": date}})



def add_played_games():
    last_games = get_last_games(date.today())
    for game in last_games:
        update_balance(game)
    played_games.insert_many(last_games)


def add_balance(home: bool, game: dict):
    balance_game = balance.find_one({"team_name": game[PLACE[home]]})
    place = SHORT_PLACE[home] + "_"
    try:
        game[place + "Last_game"] = game["days_from_start"] - balance_game["days_last"]
    except:
        print(balance)
    game[place + 'Wins'] = balance_game["wins"]
    game[place + 'Losses'] = balance_game["losses"]
    game[place + 'Difference'] = balance_game["balance"]
    try:
        game[place + 'Average_Points'] = balance_game["points"] / balance_game["game"]
    except:
        game[place + 'Average_Points'] = 0



def add_last_game(game):
    try:
        same_game = played_games.find({"$or" : 
        [{"home_group" : game["home_group"], "visitor_group" : game["visitor_group"]}, 
         {"home_group" : game["visitor_group"], "visitor_group" : game["home_group"]}]})
        same_game = max(same_game, key = lambda x: x["date"])
        game['Last_same_game'] = same_game["home_pts"] - same_game["vis_pts"]
    except:
        game['Last_same_game'] = 0



def update_next_games():
    next_games_db = list(next_games.find({}))
    last_game_date = None
    if len(next_games_db) > 0:
        last_game_date = max(next_games_db, key = lambda x: x["date"])["date"]
    for month in get_month(date.today()):
        print(month)
        if last_game_date and last_game_date > date_to_start(month):
            continue
        if month.month >= 9:
            month = date(month.year + 1, month.month, 1)
        games = scrapper.get_games(month.year, month.strftime("%B"))
        if games is None:
            break
        for game in games:
            if len(game) < 6 or game[3]:
                continue
            game_dict = {
                "date": time_from_start(game[0]), "home_group": game[4], "visitor_group": game[2]} 
            if not last_game_date or last_game_date < game_dict["date"]:
                    next_games.insert_one(game_dict)


def get_next_games(team = None) -> List[List[str]]:
    if team:
        return list(next_games.find({"$or" : [{"home_group": team}, {"visitor_group": team}]}))[:5]
    else:
        return list(next_games.find({}))[:5]




def clean_played_game(games):
    for game in next_games.find({}):
        if game["date"] < date_to_start(date.today()):
            next_games.delete_one(game)
        else:
            return


            
