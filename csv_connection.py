from textwrap import indent
from sklearn import cluster
from typing import Dict, List
from pymongo import MongoClient
import pandas as pd
import json
import sys
from datetime import date
from anylze_and_cleaning import time_from_start
sys.path.append('../AIball/Scrapper')
import scrapper

WINS = 0
LOSSES = 1
DIFFERENCE = 2
GAMES = 3
POINTS = 4
LAST = 5


class db_connection:
    def __init__(self) -> None:
        self._balance = json.load("balance.json")
        self._played_games = pd.read_csv("played_games.csv")
        self._next_games = pd.read_csv("next_games.csv")
        self._teams = json.load("")
        self._PLACE = {True: "home_group", False: "visitor_group"}
        self._SHORT_PLACE = {True:  'Hm', False: "Vis"}


    def date_to_start(self, date_to):
        return (date_to - date(date_to.year - 1, 9, 1)).days % 365

    def create_balance(self):
        open("balance.json", 'w')
        self._balance = {}
        today = date.today()
        teams = [x.split('\xa0')[0]
                 for x in scrapper.get_teams_names(today.year).keys()]
        for team in teams:
            if '*' in team:
                team = team[:-1]
            if today.month < 9:
                self._balance[team]= { "wins": 0, "losses": 0, "balance": 0, "games": 0,
                                          "points": 0, "days_last": (today - date(today.year - 1, 9, 1)).days - 15}
            else:
                self._balance[team]= {"wins": 0, "losses": 0, "balance": 0, "games": 0,
                                          "points": 0, "days_last": (today - date(today.year, 9, 1)).days - 15}
        json.dumps(self._balance,"balance.json")
    
    def get_month(self, today):
        if today.month > 9:
            year = today.year - 1
        else:
            year = today.year
        return [date(year-1, 10, 31), date(year-1, 11, 30), date(year - 1, 12, 31), date(year, 1, 31),
                date(year, 2, 28), date(year, 3, 31), date(year, 4, 30), date(year, 5, 31), date(year, 6, 30)]

    def get_last_games(self,) -> List[List[str]]:
        game_list = list()
        for month in self.get_month(date.today()):

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


    def get_last_games(self, last_game_date) -> List[List[str]]:
        game_list = list()
        for month in self.get_month(date.today()):

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


    def update_balance(self, result: Dict[str, object]):
        home_group = result['home_group']
        visitor_group = result['visitor_group']
        date = int(time_from_start(result['date']))
        if home_group not in self.balance.keys():
        # (wins, loses, balance, games, points, days from last game)
            self.balance[home_group] = [0,0,0,0,0, date - 15]
        points_result =  result['home_pts'] - result['vis_pts']
        if result['visitor_group'] not in self.balance.keys():
            self.balance[visitor_group] = [0,0,0,0,0, date - 15]
        self._balance[home_group][DIFFERENCE]+=points_result
        self._balance[home_group][GAMES]+=1
        self._balance[home_group][POINTS]+= result['home_pts']
        self._balance[home_group][LAST] = date
        self._balance[visitor_group][DIFFERENCE]-=points_result
        self._balance[visitor_group][GAMES]+=1
        self._balance[visitor_group][POINTS]+= result['vis_pts']
        self._balance[visitor_group][LAST] = date
        if points_result > 0:
            self._balance[home_group][WINS]+=1
            self._balance[visitor_group][LOSSES]+=1
        else:
            self.balance[home_group][LOSSES]+=1
            self.balance[visitor_group][WINS]+=1  
        self._last_same_game[home_group + visitor_group] = points_result
        json.dumps(self._balance,"balance.json")

    def add_balance(self, home: bool, game: dict):
        balance_game = self._balance[game[self._PLACE[home]]]
        place = self._SHORT_PLACE[home] + "_"
        try:
            game[place + "Last_game"] = game["days_from_start"] - \
                balance_game["days_last"]
        except:
            print(self._balance)
        game[place + 'Wins'] = balance_game["wins"]
        game[place + 'Losses'] = balance_game["losses"]
        game[place + 'Difference'] = balance_game["balance"]
        try:
            game[place + 'Average_Points'] = balance_game["points"] / \
                balance_game["game"]
        except:
            game[place + 'Average_Points'] = 0


    def add_played_games(self):
        last_games = self.get_last_games(date.today())
        for game in last_games:
            self.update_balance(game)
        self._played_games.insert_many(last_games)


    def add_last_game(self, game):
        try:
            same_game = self._played_games.loc[(self._played_games['home_group'] == game["home_group"] and 
            self._played_games["visitor_group"] == game["visitor_group"] )or(
            self._played_games['home_group'] == game["visitor_group"] and 
            self._played_games["visitor_group"] == game["home_group"])]
            same_game = same_game.date.max()
            game['Last_same_game'] = same_game["home_pts"] - \
                same_game["vis_pts"]
        except:
            game['Last_same_game'] = 0