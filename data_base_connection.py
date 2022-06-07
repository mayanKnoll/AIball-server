from textwrap import indent
from sklearn import cluster
from typing import Dict, List
from pymongo import MongoClient
import pandas as pd
import sys
from datetime import date
from anylze_and_cleaning import time_from_start
sys.path.append('../AIball/Scrapper')
import scrapper

# sys.path.insert(
#     0, r'..\AIball\Scrapper')


class db_connection:
    def __init__(self) -> None:
        self._cluster = MongoClient(
            "mongodb://Aiball:yuval1andmayan1@cluster0-shard-00-00.fadet.mongodb.net:27017,cluster0-shard-00-01.fadet.mongodb.net:27017,cluster0-shard-00-02.fadet.mongodb.net:27017/myFirstDatabase?ssl=true&replicaSet=atlas-11tyfk-shard-0&authSource=admin&retryWrites=true&w=majority")
        self._db = self._cluster["AIball"]
        self._balance = self._db["balance"]
        self._played_games = self._db["played_games"]
        self._next_games = self._db["next_games"]
        self._teams = self._db["teams"]
        self._PLACE = {True: "home_group", False: "visitor_group"}
        self._SHORT_PLACE = {True:  'Hm', False: "Vis"}

# next_games.delete_many({})

    def date_to_start(self, date_to):
        return (date_to - date(date_to.year - 1, 9, 1)).days % 365

    def create_balance(self):
        self._balance.delete_many({})
        today = date.today()
        teams = [x.split('\xa0')[0]
                 for x in scrapper.get_teams_names(today.year).keys()]
        for team in teams:
            if '*' in team:
                team = team[:-1]
            if today.month < 9:
                self._balance.insert_one({"team_name": team, "wins": 0, "losses": 0, "balance": 0, "games": 0,
                                          "points": 0, "days_last": (today - date(today.year - 1, 9, 1)).days - 15})
            else:
                self._balance.insert_one({"team_name": team, "wins": 0, "losses": 0, "balance": 0, "games": 0,
                                          "points": 0, "days_last": (today - date(today.year, 9, 1)).days - 15})


# {9 : date(year-1, 9, 30), 10 : date(year-1, 10, 31), 11 : date(year-1, 11, 30),
        # 12 : date(year - 1, 12, 31),1 : date(year, 1, 31),2 : date(year, 2, 28),
        # 3 : date(year, 3, 31),4 : date(year, 4, 30),5 : date(year, 5, 31), : date(year, 6, 30)}


    def get_month(self, today):
        if today.month > 9:
            year = today.year - 1
        else:
            year = today.year
        return [date(year-1, 10, 31), date(year-1, 11, 30), date(year - 1, 12, 31), date(year, 1, 31),
                date(year, 2, 28), date(year, 3, 31), date(year, 4, 30), date(year, 5, 31), date(year, 6, 30)]

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

    def update_balance(self, game_result):
        home_group = game_result['home_group']
        visitor_group = game_result['visitor_group']
        date = time_from_start(game_result['date'])
        points_result = game_result['home_pts'] - game_result['vis_pts']
        if points_result > 0:
            self._balance.update_one({"team_name": home_group}, {'$inc': {"balance": points_result,
                                                                          "games": 1, "points": game_result['home_pts'], "wins": 1}, "$set": {"date": date}})
            self._balance.update_one({"team_name": visitor_group}, {'$inc': {"balance": -points_result,
                                                                             "games": 1, "points": game_result['vis_pts'], "losses": 1}, "$set": {"date": date}})
        else:
            self._balance.update_one({"team_name": home_group}, {'$inc': {"balance": points_result,
                                                                          "games": 1, "points": game_result['home_pts'], "losses": 1}, "$set": {"days_last": date}})
            self._balance.update_one({"team_name": visitor_group}, {'$inc': {"balance": -points_result,
                                                                             "games": 1, "points": game_result['vis_pts'], "wins": 1}, "$set": {"days_last": date}})

    def add_played_games(self):
        last_games = self.get_last_games(date.today())
        for game in last_games:
            self.update_balance(game)
        self._played_games.insert_many(last_games)

    def add_balance(self, home: bool, game: dict):
        balance_game = self._balance.find_one(
            {"team_name": game[self._PLACE[home]]})
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

    def add_last_game(self, game):
        try:
            same_game = self.played_games.find({"$or":
                                                [{"home_group": game["home_group"], "visitor_group": game["visitor_group"]},
                                                 {"home_group": game["visitor_group"], "visitor_group": game["home_group"]}]})
            same_game = max(same_game, key=lambda x: x["date"])
            game['Last_same_game'] = same_game["home_pts"] - \
                same_game["vis_pts"]
        except:
            game['Last_same_game'] = 0

    def update_next_games(self):
        next_games_db = list(self._next_games.find({}))
        last_game_date = None
        if len(next_games_db) > 0:
            last_game_date = max(
                next_games_db, key=lambda x: x["date"])["date"]
        for month in self.get_month(date.today()):
            print(month)
            if last_game_date and last_game_date > self.date_to_start(month):
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
                    "date": game[0], "home_group": game[4], "visitor_group": game[2]}
                if not last_game_date or last_game_date < game_dict["date"]:
                    self._next_games.insert_one(game_dict)

    def get_next_games(self, team=None) -> List[List[str]]:
        if team:
            return list(self._next_games.find({"$or": [{"home_group": {"$regex": team}}, {"visitor_group": {"$regex": team}}]}).limit(5))
        else:
            return list(self._next_games.find({}).limit(5))

    def clean_played_game(self, games):
        for game in self._next_games.find({}):
            if game["date"] < self.date_to_start(date.today()):
                self._next_games.delete_one(game)
            else:
                return

    def upload_teams(self, path):

        teams_df = pd.read_csv(path)
        for index in teams_df.index:
            team = dict()
            for col in teams_df.columns:
                if(col == "index"):
                    key = "_id"
                else:
                    key = col
                team[key] = str(teams_df.loc[index, col])
            print(teams_df.loc[index, "index"])
            self._teams.insert_one(team)

    def get_team(self, year: str, team: str) -> Dict[str, str]:
        return self._teams.find_one({"_id": str(year)+team}, {"_id": 0})

    def get_teams_name(self):
        team_set = set(self._next_games.distinct('home_group'))
        team_set.update(self._next_games.distinct('home_group'))
        return team_set
